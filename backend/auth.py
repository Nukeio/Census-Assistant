"""
Census Assistant - Authentication & Authorization Layer
Supports:
- Field Functionary OTP Mobile Verification
- User Registration & Password Authentication (PBKDF2-SHA256 with 260,000 iterations & random salt)
- Administrator Authentication & Role-Based Access Control (RBAC)
- Secure Password Reset with Time-Limited Tokens
- Optional Supabase Auth Integration for Cloud Deployments
"""

import os
import time
import hashlib
import hmac
import random
import logging
import secrets
from typing import Dict, Any, Optional, Tuple
import requests
import jwt
from .database import get_db_connection

logger = logging.getLogger("AuthService")
logging.basicConfig(level=logging.INFO)

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    JWT_SECRET = "census-assistant-super-secret-key-2024"
    logger.warning(
        "JWT_SECRET is not set — using default signing key. "
        "Set the JWT_SECRET environment variable for production."
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

# Optional Supabase Auth configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Dev-only convenience for local testing without SMS gateways
DEV_OTP_BYPASS = os.environ.get("DEV_OTP_BYPASS", "false").lower() in ("1", "true", "yes")

# In-memory OTP store: mobile -> {otp, expires_at, request_count, window_start}
OTP_STORE: Dict[str, Dict[str, Any]] = {}
OTP_RATE_MAX = 5          # Maximum OTP requests per mobile per window
OTP_RATE_WINDOW = 300     # Window duration in seconds (5 minutes)

# Password-guessing throttle. Counters live in the database rather than in
# memory so they survive the worker recycling that PythonAnywhere does
# routinely — an attacker cannot reset the count by waiting for a restart.
LOGIN_MAX_ATTEMPTS = 6
LOGIN_LOCKOUT_SECONDS = 900   # 15 minutes
MIN_PASSWORD_LENGTH = 8

# ---------------------------------------------------------------------------
# PBKDF2 Password Hashing
# ---------------------------------------------------------------------------
PBKDF2_ITERATIONS = 260_000
PBKDF2_HASH = "sha256"

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    Produce a PBKDF2-SHA256 hash of *password* in format:
        pbkdf2$sha256$<iterations>$<hex_salt>$<hex_digest>
    """
    if salt is None:
        salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac(
        PBKDF2_HASH,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2${PBKDF2_HASH}${PBKDF2_ITERATIONS}${salt}${dk.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify *password* against stored PBKDF2 or legacy SHA-256 hash using
    constant-time comparison to prevent timing attacks.
    """
    if not stored_hash or not password:
        return False
    if stored_hash.startswith("pbkdf2$"):
        try:
            _, alg, iters_str, salt, expected_dk = stored_hash.split("$")
            iters = int(iters_str)
            dk = hashlib.pbkdf2_hmac(
                alg,
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iters,
            )
            return hmac.compare_digest(dk.hex(), expected_dk)
        except Exception as e:
            logger.error(f"PBKDF2 verification error: {e}")
            return False
    else:
        # Legacy SHA-256 fallback
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        return hmac.compare_digest(legacy_hash, stored_hash)

# ---------------------------------------------------------------------------
# Audit trail & login throttling
# ---------------------------------------------------------------------------

def audit(event: str, account: str = "", outcome: str = "", detail: str = "",
          actor: str = "", ip_address: str = "") -> None:
    """
    Record an authentication event. Never raises — an audit write failing must
    not be able to block a legitimate sign-in.
    """
    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO auth_audit (account, event, outcome, detail, actor, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (account, event, outcome, detail, actor, ip_address))
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning(f"Could not write auth audit row ({event}): {exc}")


def _row_value(row, key: str, default=None):
    """Read a column that may be absent on a row from an un-migrated table."""
    try:
        value = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if value is None else value


def _lockout_remaining(row) -> int:
    """Seconds left on an account lockout, or 0 if it isn't locked."""
    locked_until = _row_value(row, "locked_until", 0)
    return max(0, int(locked_until - time.time()))


def _register_failed_attempt(conn, table: str, row_id: int, attempts: int) -> int:
    """
    Bump the failure counter and lock the account once it crosses the limit.
    Returns the lockout duration applied, or 0 if not yet locked.

    The counters live in the database rather than in memory so they survive
    the worker recycling PythonAnywhere does routinely — an attacker cannot
    clear the count by waiting for a restart.
    """
    attempts = (attempts or 0) + 1
    if attempts >= LOGIN_MAX_ATTEMPTS:
        conn.execute(
            f"UPDATE {table} SET failed_attempts = ?, locked_until = ? WHERE id = ?",
            (attempts, time.time() + LOGIN_LOCKOUT_SECONDS, row_id),
        )
        conn.commit()
        return LOGIN_LOCKOUT_SECONDS
    conn.execute(f"UPDATE {table} SET failed_attempts = ? WHERE id = ?", (attempts, row_id))
    conn.commit()
    return 0


def _clear_failed_attempts(conn, table: str, row_id: int) -> None:
    """Reset the throttle and stamp the successful sign-in."""
    conn.execute(
        f"""UPDATE {table}
            SET failed_attempts = 0, locked_until = NULL, last_login_at = CURRENT_TIMESTAMP
            WHERE id = ?""",
        (row_id,),
    )
    conn.commit()


def _lockout_message(seconds: int) -> str:
    minutes = max(1, round(seconds / 60))
    return (
        f"Too many failed sign-in attempts. This account is locked for about "
        f"{minutes} minute{'s' if minutes != 1 else ''}. "
        "Contact the Technical Assistant if you need it unlocked sooner."
    )


def validate_password_strength(password: str) -> Optional[str]:
    """Return an error message if the password is too weak, else None."""
    password = password or ""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
    if password.isdigit():
        return "Password cannot be only numbers. Add some letters to make it harder to guess."
    if password.lower() in ("password", "12345678", "census2027", "qwertyui", "asdfghjk"):
        return "That password is too easy to guess. Please choose a different one."
    return None


def generate_temporary_password() -> str:
    """
    A readable one-time password for the office counter: two short letter
    groups plus digits, avoiding characters that are easy to misread aloud
    (0/O, 1/l/I). Long enough to resist guessing, short enough to dictate.
    """
    letters = "abcdefghjkmnpqrstuvwxyz"
    digits = "23456789"
    part = "".join(secrets.choice(letters) for _ in range(4))
    tail = "".join(secrets.choice(digits) for _ in range(4))
    return f"{part.capitalize()}{tail}"


# ---------------------------------------------------------------------------
# JWT Token Helpers
# ---------------------------------------------------------------------------

def generate_jwt_token(user_data: Dict[str, Any]) -> str:
    """Generate signed JWT token with standard claims and custom roles."""
    now = time.time()
    payload = {
        "sub": str(user_data.get("user_id") or user_data.get("username") or "guest"),
        "name": user_data.get("name") or user_data.get("full_name") or "User",
        "role": user_data.get("role", "user"),
        "mobile": user_data.get("mobile_number", ""),
        "email": user_data.get("email", ""),
        "functionary_type": user_data.get("functionary_type", "User"),
        # Carried in the token so every request can tell that this session is
        # running on an admin-issued temporary password and must not be
        # allowed to do anything except set a new one.
        "must_change_password": bool(user_data.get("must_change_password")),
        "exp": now + (JWT_EXPIRATION_HOURS * 3600),
        "iat": now
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token (supports local JWT & Supabase JWT if configured)."""
    if not token:
        return None

    # 1. Try local JWT verification
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        pass

    # 2. Try Supabase Auth verification if Supabase is configured
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        try:
            headers = {
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}"
            }
            resp = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers, timeout=5)
            if resp.status_code == 200:
                sb_user = resp.json()
                app_metadata = sb_user.get("app_metadata", {})
                user_metadata = sb_user.get("user_metadata", {})
                return {
                    "sub": sb_user.get("id"),
                    "name": user_metadata.get("name") or user_metadata.get("full_name") or "Supabase User",
                    "role": app_metadata.get("role") or user_metadata.get("role") or "user",
                    "email": sb_user.get("email", ""),
                    "mobile": sb_user.get("phone", "") or user_metadata.get("mobile", ""),
                    "functionary_type": user_metadata.get("functionary_type", "User")
                }
        except Exception as e:
            logger.debug(f"Supabase token verification check: {e}")

    return None

# ---------------------------------------------------------------------------
# Guest Session
# ---------------------------------------------------------------------------

def create_guest_session() -> Dict[str, Any]:
    """Create a guest session token."""
    user_data = {
        "user_id": f"guest_{int(time.time())}",
        "name": "Guest Visitor",
        "role": "guest",
        "functionary_type": "Guest Access",
        "mobile_number": ""
    }
    token = generate_jwt_token(user_data)
    return {
        "success": True,
        "authenticated": True,
        "token": token,
        "user": user_data
    }

# ---------------------------------------------------------------------------
# User Registration & Password Login
# ---------------------------------------------------------------------------

def register_user(name: str, mobile_number: str, password: str, email: Optional[str] = None) -> Dict[str, Any]:
    """
    Register a new user account with secure PBKDF2 password hashing.
    If the mobile number matches an existing Census Functionary, automatically
    links the supervisor/enumerator profile.
    """
    name = (name or "").strip()
    password = (password or "").strip()
    email = (email or "").strip().lower() or None
    clean_mobile = "".join([c for c in (mobile_number or "") if c.isdigit()])
    if len(clean_mobile) > 10:
        clean_mobile = clean_mobile[-10:]

    if len(name) < 2:
        return {"success": False, "message": "Please enter a valid full name."}
    if len(clean_mobile) != 10:
        return {"success": False, "message": "Please enter a valid 10-digit mobile number."}
    weak = validate_password_strength(password)
    if weak:
        return {"success": False, "message": weak}

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if mobile already registered in app_users
    cursor.execute("SELECT id FROM app_users WHERE mobile_number = ?", (clean_mobile,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "message": "An account with this mobile number already exists. Please sign in."}

    # Check if email already registered
    if email:
        cursor.execute("SELECT id FROM app_users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "message": "An account with this email address already exists."}

    # Check if mobile belongs to an official Census Functionary in records
    cursor.execute("""
        SELECT * FROM functionaries 
        WHERE mobile_number LIKE ? OR mobile_number LIKE ?
        LIMIT 1
    """, (f"%{clean_mobile}%", clean_mobile))
    func = cursor.fetchone()

    role = "user"
    functionary_type = "User"
    user_id = f"usr_{clean_mobile}"

    if func:
        role = "supervisor" if "Supervisor" in (func["functionary_type"] or "") else "enumerator"
        functionary_type = func["functionary_type"] or "Field Enumerator"
        user_id = func["user_id"] or user_id
        if not name:
            name = func["name"]

    pass_hash = hash_password(password)

    try:
        cursor.execute("""
            INSERT INTO app_users (user_id, mobile_number, email, name, password_hash, role, functionary_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, clean_mobile, email, name, pass_hash, role, functionary_type))
        conn.commit()
    except Exception as e:
        conn.close()
        logger.error(f"User registration error: {e}")
        return {"success": False, "message": "Could not create account. Please try again."}

    conn.close()

    user_data = {
        "user_id": user_id,
        "name": name,
        "mobile_number": clean_mobile,
        "email": email or "",
        "role": role,
        "functionary_type": functionary_type
    }
    token = generate_jwt_token(user_data)

    audit("register", clean_mobile, "success", f"role={role}")

    return {
        "success": True,
        "message": "Account created successfully.",
        "token": token,
        "user": user_data
    }

def login_user(identifier: str, password: str, ip_address: str = "") -> Dict[str, Any]:
    """
    Authenticate a user or admin by mobile number, username, or email.

    Checks admin_users first, then app_users. Both tables are throttled: after
    LOGIN_MAX_ATTEMPTS consecutive failures the account is locked for
    LOGIN_LOCKOUT_SECONDS. Every outcome is written to auth_audit.

    The failure message is deliberately identical whether the account does not
    exist or the password is wrong, so the endpoint cannot be used to discover
    which mobile numbers are registered.
    """
    identifier = (identifier or "").strip()
    password = (password or "").strip()
    generic_failure = "Invalid username, mobile number, or password."

    if not identifier or not password:
        return {"success": False, "message": "Please enter your username/mobile and password."}

    clean_digits = "".join([c for c in identifier if c.isdigit()])
    if len(clean_digits) > 10:
        clean_digits = clean_digits[-10:]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ---------------- 1. Administrator accounts ----------------
        cursor.execute(
            "SELECT * FROM admin_users WHERE username = ? OR username = ?",
            (identifier, identifier.lower()),
        )
        admin = cursor.fetchone()
        if admin:
            locked = _lockout_remaining(admin)
            if locked:
                audit("admin_login", identifier, "locked", f"{locked}s remaining", ip_address=ip_address)
                return {"success": False, "locked": True, "message": _lockout_message(locked)}

            if verify_password(password, admin["password_hash"]):
                _clear_failed_attempts(conn, "admin_users", admin["id"])
                user_data = {
                    "user_id": f"admin_{admin['id']}",
                    "username": admin["username"],
                    "name": admin["full_name"] or "System Administrator",
                    "role": "admin",
                    "functionary_type": "System Administrator",
                    "must_change_password": bool(_row_value(admin, "must_change_password", 0)),
                }
                audit("admin_login", identifier, "success", ip_address=ip_address)
                return {
                    "success": True,
                    "token": generate_jwt_token(user_data),
                    "user": user_data,
                    "must_change_password": user_data["must_change_password"],
                }

            lockout = _register_failed_attempt(
                conn, "admin_users", admin["id"], _row_value(admin, "failed_attempts", 0)
            )
            audit("admin_login", identifier, "failure", "bad password", ip_address=ip_address)
            if lockout:
                return {"success": False, "locked": True, "message": _lockout_message(lockout)}
            return {"success": False, "message": generic_failure}

        # ---------------- 2. Application user accounts ----------------
        cursor.execute("""
            SELECT * FROM app_users
            WHERE user_id = ? OR mobile_number = ? OR email = ? OR LOWER(email) = ?
            LIMIT 1
        """, (identifier,
              clean_digits if len(clean_digits) == 10 else identifier,
              identifier,
              identifier.lower()))
        user = cursor.fetchone()

        if not user:
            audit("login", identifier, "failure", "no such account", ip_address=ip_address)
            return {"success": False, "message": generic_failure}

        if str(_row_value(user, "status", "ACTIVE")).upper() != "ACTIVE":
            audit("login", identifier, "failure", "account disabled", ip_address=ip_address)
            return {
                "success": False,
                "message": "This account has been disabled. Please contact the Technical Assistant.",
            }

        locked = _lockout_remaining(user)
        if locked:
            audit("login", identifier, "locked", f"{locked}s remaining", ip_address=ip_address)
            return {"success": False, "locked": True, "message": _lockout_message(locked)}

        if not verify_password(password, user["password_hash"]):
            lockout = _register_failed_attempt(
                conn, "app_users", user["id"], _row_value(user, "failed_attempts", 0)
            )
            audit("login", identifier, "failure", "bad password", ip_address=ip_address)
            if lockout:
                return {"success": False, "locked": True, "message": _lockout_message(lockout)}
            return {"success": False, "message": generic_failure}

        _clear_failed_attempts(conn, "app_users", user["id"])
        must_change = bool(_row_value(user, "must_change_password", 0))
        user_data = {
            "user_id": user["user_id"],
            "name": user["name"],
            "mobile_number": user["mobile_number"],
            "email": user["email"] or "",
            "role": user["role"] or "user",
            "functionary_type": user["functionary_type"] or "User",
            "must_change_password": must_change,
        }
        audit("login", identifier, "success",
              "temporary password" if must_change else "", ip_address=ip_address)
        return {
            "success": True,
            "token": generate_jwt_token(user_data),
            "user": user_data,
            "must_change_password": must_change,
            "message": (
                "Signed in with a temporary password. Please set a new password now."
                if must_change else "Signed in successfully."
            ),
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Password self-service & admin-assisted reset
# ---------------------------------------------------------------------------

def _find_account(cursor, identifier: str):
    """
    Locate an account by user_id, mobile number, email or admin username.
    Returns (table_name, row) or (None, None).
    """
    identifier = (identifier or "").strip()
    clean_digits = "".join([c for c in identifier if c.isdigit()])
    if len(clean_digits) > 10:
        clean_digits = clean_digits[-10:]

    cursor.execute("""
        SELECT * FROM app_users
        WHERE user_id = ? OR mobile_number = ? OR LOWER(email) = ?
        LIMIT 1
    """, (identifier,
          clean_digits if len(clean_digits) == 10 else identifier,
          identifier.lower()))
    row = cursor.fetchone()
    if row:
        return "app_users", row

    cursor.execute(
        "SELECT * FROM admin_users WHERE username = ? OR username = ?",
        (identifier, identifier.lower()),
    )
    row = cursor.fetchone()
    if row:
        return "admin_users", row
    return None, None


def change_password(identifier: str, current_password: str, new_password: str,
                    ip_address: str = "") -> Dict[str, Any]:
    """
    Change a password from inside an authenticated session.

    This is the endpoint a user lands on after signing in with an
    admin-issued temporary password, and it is also how anyone changes their
    own password voluntarily. Clearing must_change_password here is what
    releases the account back to normal use.
    """
    weak = validate_password_strength(new_password)
    if weak:
        return {"success": False, "message": weak}

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        table, row = _find_account(cursor, identifier)
        if not row:
            return {"success": False, "message": "Account not found."}

        if not verify_password(current_password or "", row["password_hash"]):
            audit("password_change", identifier, "failure", "wrong current password", ip_address=ip_address)
            return {"success": False, "message": "Your current password is not correct."}

        if verify_password(new_password, row["password_hash"]):
            return {"success": False, "message": "Please choose a password you have not used before."}

        conn.execute(
            f"""UPDATE {table}
                SET password_hash = ?, must_change_password = 0,
                    reset_token = NULL, reset_token_expires = NULL,
                    failed_attempts = 0, locked_until = NULL
                WHERE id = ?""",
            (hash_password(new_password), row["id"]),
        )
        conn.commit()
        audit("password_change", identifier, "success", ip_address=ip_address)
        return {"success": True, "message": "Password updated. Please use it the next time you sign in."}
    finally:
        conn.close()


def admin_reset_user_password(identifier: str, actor: str = "admin") -> Dict[str, Any]:
    """
    Issue a temporary password for a user who has forgotten theirs.

    This is the counter workflow: the user comes to the office, the Technical
    Assistant runs this, reads out the one-time password, and the user is
    forced to choose their own on the next sign-in. The stored value is a
    PBKDF2 hash exactly like any other password — the plain text exists only
    in this single response and is never written to the database or the log.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        table, row = _find_account(cursor, identifier)
        if not row:
            return {"success": False, "message": "No account found for that mobile number or username."}

        temporary = generate_temporary_password()
        conn.execute(
            f"""UPDATE {table}
                SET password_hash = ?, must_change_password = 1,
                    failed_attempts = 0, locked_until = NULL,
                    reset_token = NULL, reset_token_expires = NULL
                WHERE id = ?""",
            (hash_password(temporary), row["id"]),
        )
        conn.commit()

        display_name = _row_value(row, "name", "") or _row_value(row, "full_name", "") or identifier
        account = _row_value(row, "mobile_number", "") or _row_value(row, "username", "") or identifier
        audit("admin_password_reset", str(account), "success",
              f"temporary password issued for {display_name}", actor=actor)

        return {
            "success": True,
            "message": f"Temporary password issued for {display_name}.",
            "name": display_name,
            "account": str(account),
            "temporary_password": temporary,
            "note": "Give this to the user in person. They must set their own password at the next sign-in.",
        }
    finally:
        conn.close()


def admin_unlock_account(identifier: str, actor: str = "admin") -> Dict[str, Any]:
    """Clear a lockout without touching the password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        table, row = _find_account(cursor, identifier)
        if not row:
            return {"success": False, "message": "No account found for that mobile number or username."}
        conn.execute(
            f"UPDATE {table} SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
            (row["id"],),
        )
        conn.commit()
        audit("admin_unlock", identifier, "success", actor=actor)
        return {"success": True, "message": "Account unlocked."}
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------

def request_password_reset(identifier: str, ip_address: str = "") -> Dict[str, Any]:
    """
    Issue a time-limited reset code for an account.

    Works for both app_users and admin_users — a previous version generated a
    code for administrators but only ever stored it on app_users, so an admin
    reset appeared to succeed and then always rejected the code.

    There is no SMS or email gateway configured on this deployment, so the
    code is written to the server log for the Technical Assistant to relay.
    The response says exactly that rather than implying a message was sent,
    and it never echoes the code to the caller outside DEV_OTP_BYPASS — that
    would let anyone reset any account they can name.
    """
    identifier = (identifier or "").strip()
    if not identifier:
        return {"success": False, "message": "Enter your mobile number or username."}

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        table, row = _find_account(cursor, identifier)
        if not row:
            # Uniform response: do not reveal which accounts exist.
            audit("password_reset_request", identifier, "failure", "no such account", ip_address=ip_address)
            return {
                "success": True,
                "message": (
                    "If an account matches those details, a reset code has been issued. "
                    "Contact the Technical Assistant to receive it."
                ),
                "identifier": identifier,
            }

        reset_code = f"{secrets.randbelow(1000000):06d}"
        conn.execute(
            f"UPDATE {table} SET reset_token = ?, reset_token_expires = ? WHERE id = ?",
            (reset_code, time.time() + 900, row["id"]),
        )
        conn.commit()

        logger.info(f"[PASSWORD RESET] Code for {identifier}: {reset_code} (valid 15 minutes)")
        audit("password_reset_request", identifier, "success", ip_address=ip_address)

        res = {
            "success": True,
            "message": (
                "If an account matches those details, a reset code has been issued. "
                "Contact the Technical Assistant to receive it."
            ),
            "identifier": identifier,
        }
        if DEV_OTP_BYPASS:
            res["debug_reset_code"] = reset_code
        return res
    finally:
        conn.close()

def complete_password_reset(identifier: str, reset_code: str, new_password: str,
                            ip_address: str = "") -> Dict[str, Any]:
    """
    Complete a password reset with a valid, unexpired code.

    Covers administrators as well as app users — the previous version only
    looked in app_users, so an administrator could never finish a reset.
    """
    identifier = (identifier or "").strip()
    reset_code = (reset_code or "").strip()
    new_password = (new_password or "").strip()

    weak = validate_password_strength(new_password)
    if weak:
        return {"success": False, "message": weak}

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        table, row = _find_account(cursor, identifier)
        if not row:
            audit("password_reset", identifier, "failure", "no such account", ip_address=ip_address)
            return {"success": False, "message": "Invalid or expired password reset code."}

        stored = _row_value(row, "reset_token", "")
        expires = _row_value(row, "reset_token_expires", 0)

        # compare_digest so a wrong code cannot be discovered a character at a
        # time from response timing.
        if not stored or not hmac.compare_digest(str(stored), reset_code):
            audit("password_reset", identifier, "failure", "bad code", ip_address=ip_address)
            return {"success": False, "message": "Invalid or expired password reset code."}

        if expires < time.time():
            audit("password_reset", identifier, "failure", "expired code", ip_address=ip_address)
            return {"success": False, "message": "That reset code has expired. Please request a new one."}

        conn.execute(
            f"""UPDATE {table}
                SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL,
                    must_change_password = 0, failed_attempts = 0, locked_until = NULL
                WHERE id = ?""",
            (hash_password(new_password), row["id"]),
        )
        conn.commit()
        audit("password_reset", identifier, "success", ip_address=ip_address)
        return {"success": True, "message": "Password updated. You can now sign in with your new password."}
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# OTP Verification (Field Functionaries)
# ---------------------------------------------------------------------------

def _check_otp_rate_limit(mobile: str) -> Tuple[bool, str]:
    now = time.time()
    entry = OTP_STORE.get(mobile, {})
    window_start = entry.get("window_start", 0)
    count = entry.get("request_count", 0)

    if now - window_start > OTP_RATE_WINDOW:
        return True, ""

    if count >= OTP_RATE_MAX:
        remaining = int(OTP_RATE_WINDOW - (now - window_start))
        return False, f"Too many OTP requests. Please wait {remaining} seconds before trying again."

    return True, ""

def request_otp(mobile_number: str) -> Dict[str, Any]:
    clean_mobile = "".join([c for c in mobile_number if c.isdigit()])
    if len(clean_mobile) > 10:
        clean_mobile = clean_mobile[-10:]

    if len(clean_mobile) < 10:
        return {"success": False, "message": "Please enter a valid 10-digit mobile number."}

    allowed, rate_msg = _check_otp_rate_limit(clean_mobile)
    if not allowed:
        return {"success": False, "message": rate_msg}

    otp_code = str(random.randint(100000, 999999))
    now = time.time()

    existing = OTP_STORE.get(clean_mobile, {})
    window_start = existing.get("window_start", now) if (now - existing.get("window_start", 0)) <= OTP_RATE_WINDOW else now
    request_count = existing.get("request_count", 0) + 1 if (now - existing.get("window_start", 0)) <= OTP_RATE_WINDOW else 1

    OTP_STORE[clean_mobile] = {
        "otp": otp_code,
        "expires_at": now + 600,
        "window_start": window_start,
        "request_count": request_count
    }

    logger.info(f"[OTP SEND] Generated OTP for {clean_mobile}: {otp_code}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM functionaries 
        WHERE mobile_number LIKE ? OR mobile_number LIKE ?
        LIMIT 1
    """, (f"%{clean_mobile}%", clean_mobile))
    func = cursor.fetchone()
    conn.close()

    user_info = None
    if func:
        user_info = {
            "name": func["name"],
            "user_id": func["user_id"],
            "role": "supervisor" if "Supervisor" in (func["functionary_type"] or "") else "enumerator",
            "functionary_type": func["functionary_type"]
        }

    response = {
        "success": True,
        "message": f"OTP sent successfully to +91 {clean_mobile}",
        "mobile": clean_mobile,
        "is_registered": bool(func),
        "user_info": user_info
    }
    if DEV_OTP_BYPASS:
        response["debug_otp"] = otp_code
    return response

def verify_otp(mobile_number: str, otp: str) -> Dict[str, Any]:
    clean_mobile = "".join([c for c in mobile_number if c.isdigit()])
    if len(clean_mobile) > 10:
        clean_mobile = clean_mobile[-10:]

    stored = OTP_STORE.get(clean_mobile)
    bypass_ok = DEV_OTP_BYPASS and otp == "123456"

    if not stored and not bypass_ok:
        return {"success": False, "message": "OTP expired or not requested. Please request again."}

    if stored and stored["expires_at"] < time.time() and not bypass_ok:
        return {"success": False, "message": "OTP has expired. Please request a new one."}

    if stored and stored["otp"] != otp and not bypass_ok:
        return {"success": False, "message": "Invalid OTP code. Please check and re-enter."}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM functionaries 
        WHERE mobile_number LIKE ? OR mobile_number LIKE ?
        LIMIT 1
    """, (f"%{clean_mobile}%", clean_mobile))
    func = cursor.fetchone()
    conn.close()

    if func:
        role = "supervisor" if "Supervisor" in (func["functionary_type"] or "") else "enumerator"
        user_data = {
            "user_id": func["user_id"],
            "name": func["name"],
            "role": role,
            "functionary_type": func["functionary_type"],
            "mobile_number": func["mobile_number"],
            "district": func["district"],
            "sub_district": func["sub_district"],
            "status": func["status"]
        }
    else:
        user_data = {
            "user_id": f"field_user_{clean_mobile}",
            "name": f"Field User ({clean_mobile})",
            "role": "enumerator",
            "functionary_type": "Field Enumerator",
            "mobile_number": clean_mobile
        }

    token = generate_jwt_token(user_data)
    if clean_mobile in OTP_STORE:
        OTP_STORE[clean_mobile]["otp"] = None
        OTP_STORE[clean_mobile]["expires_at"] = 0

    return {
        "success": True,
        "token": token,
        "user": user_data
    }

# ---------------------------------------------------------------------------
# Admin Login
# ---------------------------------------------------------------------------

def admin_login(username: str, password: str, ip_address: str = "") -> Dict[str, Any]:
    """
    Authenticate administrator credentials using PBKDF2 verification.

    Throttled and audited on the same terms as login_user — the admin account
    is the most valuable target in the system, so it gets the same lockout
    rather than an unlimited guessing budget.
    """
    username = (username or "").strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM admin_users WHERE username = ? OR username = ?",
            (username, username.lower()),
        )
        admin = cursor.fetchone()

        if not admin:
            audit("admin_login", username, "failure", "no such admin", ip_address=ip_address)
            return {"success": False, "message": "Invalid admin username or password."}

        locked = _lockout_remaining(admin)
        if locked:
            audit("admin_login", username, "locked", f"{locked}s remaining", ip_address=ip_address)
            return {"success": False, "locked": True, "message": _lockout_message(locked)}

        if not verify_password(password, admin["password_hash"]):
            lockout = _register_failed_attempt(
                conn, "admin_users", admin["id"], _row_value(admin, "failed_attempts", 0)
            )
            audit("admin_login", username, "failure", "bad password", ip_address=ip_address)
            if lockout:
                return {"success": False, "locked": True, "message": _lockout_message(lockout)}
            return {"success": False, "message": "Invalid admin username or password."}

        _clear_failed_attempts(conn, "admin_users", admin["id"])
        must_change = bool(_row_value(admin, "must_change_password", 0))
        user_data = {
            "user_id": f"admin_{admin['id']}",
            "username": admin["username"],
            "name": admin["full_name"] or "Census System Admin",
            "role": "admin",
            "functionary_type": "System Administrator",
            "must_change_password": must_change,
        }
        audit("admin_login", username, "success", ip_address=ip_address)
        return {
            "success": True,
            "token": generate_jwt_token(user_data),
            "user": user_data,
            "must_change_password": must_change,
        }
    finally:
        conn.close()
