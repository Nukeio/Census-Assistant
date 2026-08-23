"""
Census Assistant - Authentication & Authorization Layer
Handles Guest Access, OTP Mobile Verification for Field Functionaries, and Admin Login with JWT Tokens.
"""

import os
import time
import hashlib
import hmac
import random
import logging
from typing import Dict, Any, Optional, Tuple
import jwt
from .database import get_db_connection

logger = logging.getLogger("AuthService")
logging.basicConfig(level=logging.INFO)

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    JWT_SECRET = "census-assistant-super-secret-key-2024"
    logger.warning(
        "JWT_SECRET is not set — using an insecure default signing key. "
        "Set the JWT_SECRET environment variable before deploying this app."
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

# Dev-only convenience: when true, OTP endpoints echo the generated code back
# in the API response and accept a universal "123456" bypass code. This must
# stay OFF in any real deployment — otherwise anyone can authenticate as any
# mobile number without ever receiving an SMS.
DEV_OTP_BYPASS = os.environ.get("DEV_OTP_BYPASS", "false").lower() in ("1", "true", "yes")

# In-memory OTP store: mobile -> {otp, expires_at, request_count, window_start}
# Added request_count and window_start for rate-limiting (max 3 requests per mobile per 5 minutes).
OTP_STORE: Dict[str, Dict[str, Any]] = {}

OTP_RATE_MAX = 3          # Maximum OTP requests per mobile per window
OTP_RATE_WINDOW = 300     # Window duration in seconds (5 minutes)

# ---------------------------------------------------------------------------
# PBKDF2 password hashing (replaces plain SHA-256 with no salt)
# ---------------------------------------------------------------------------
PBKDF2_ITERATIONS = 260_000
PBKDF2_HASH = "sha256"

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    Produce a PBKDF2-SHA256 hash of *password* in the format:
        pbkdf2$sha256$<iterations>$<hex_salt>$<hex_digest>
    If *salt* is not supplied, a random 16-byte salt is generated.
    Returns the full self-describing string so the hash and its parameters
    travel together and can be verified without any out-of-band state.
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
    Verify *password* against a stored hash string.
    Supports both the new 'pbkdf2$...' format and the legacy plain SHA-256
    hex digest (so old rows in the DB keep working until they are re-seeded).
    Uses hmac.compare_digest throughout to prevent timing attacks.
    """
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
        # Legacy SHA-256 path — kept only for backward compatibility
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        return hmac.compare_digest(legacy_hash, stored_hash)

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def generate_jwt_token(user_data: Dict[str, Any]) -> str:
    """Generate signed JWT token."""
    payload = {
        "sub": user_data.get("user_id") or user_data.get("username") or "guest",
        "name": user_data.get("name") or user_data.get("full_name") or "Guest User",
        "role": user_data.get("role", "guest"),
        "mobile": user_data.get("mobile_number", ""),
        "functionary_type": user_data.get("functionary_type", "Guest"),
        "exp": time.time() + (JWT_EXPIRATION_HOURS * 3600),
        "iat": time.time()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception as e:
        logger.debug(f"Invalid JWT: {e}")
        return None

# ---------------------------------------------------------------------------
# Guest session
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
# OTP helpers
# ---------------------------------------------------------------------------

def _check_otp_rate_limit(mobile: str) -> Tuple[bool, str]:
    """
    Enforce rate limiting: max OTP_RATE_MAX requests per mobile per OTP_RATE_WINDOW seconds.
    Returns (allowed: bool, message: str).
    """
    now = time.time()
    entry = OTP_STORE.get(mobile, {})
    window_start = entry.get("window_start", 0)
    count = entry.get("request_count", 0)

    if now - window_start > OTP_RATE_WINDOW:
        # Window expired — reset counter
        return True, ""

    if count >= OTP_RATE_MAX:
        remaining = int(OTP_RATE_WINDOW - (now - window_start))
        return False, f"Too many OTP requests. Please wait {remaining} seconds before trying again."

    return True, ""

def request_otp(mobile_number: str) -> Dict[str, Any]:
    """Generate and send 6-digit OTP for a mobile number."""
    clean_mobile = "".join([c for c in mobile_number if c.isdigit()])
    if len(clean_mobile) > 10:
        clean_mobile = clean_mobile[-10:]

    if len(clean_mobile) < 10:
        return {"success": False, "message": "Please enter a valid 10-digit mobile number."}

    # Rate limit check
    allowed, rate_msg = _check_otp_rate_limit(clean_mobile)
    if not allowed:
        return {"success": False, "message": rate_msg}

    otp_code = str(random.randint(100000, 999999))
    now = time.time()

    # Preserve the window_start if still within the current window
    existing = OTP_STORE.get(clean_mobile, {})
    window_start = existing.get("window_start", now) if (now - existing.get("window_start", 0)) <= OTP_RATE_WINDOW else now
    request_count = existing.get("request_count", 0) + 1 if (now - existing.get("window_start", 0)) <= OTP_RATE_WINDOW else 1

    OTP_STORE[clean_mobile] = {
        "otp": otp_code,
        "expires_at": now + 600,   # 10-minute validity
        "window_start": window_start,
        "request_count": request_count
    }

    logger.info(f"[OTP SEND] Generated OTP for {clean_mobile}: {otp_code} (request #{request_count} in window)")

    # Check if this mobile exists in functionaries table
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
        # Only ever included when DEV_OTP_BYPASS is explicitly enabled for local testing.
        response["debug_otp"] = otp_code
    return response

def verify_otp(mobile_number: str, otp: str) -> Dict[str, Any]:
    """Verify OTP and authenticate user."""
    clean_mobile = "".join([c for c in mobile_number if c.isdigit()])
    if len(clean_mobile) > 10:
        clean_mobile = clean_mobile[-10:]

    stored = OTP_STORE.get(clean_mobile)
    # The '123456' bypass code only works when DEV_OTP_BYPASS is explicitly enabled
    # (local testing). In a real deployment this path is disabled entirely.
    bypass_ok = DEV_OTP_BYPASS and otp == "123456"

    if not stored and not bypass_ok:
        return {"success": False, "message": "OTP expired or not requested. Please request again."}

    if stored and stored["expires_at"] < time.time() and not bypass_ok:
        return {"success": False, "message": "OTP has expired. Please request a new one."}

    if stored and stored["otp"] != otp and not bypass_ok:
        return {"success": False, "message": "Invalid OTP code. Please check and re-enter."}

    # Retrieve functionary profile
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
        # Verified mobile number but not in census records — grant limited access
        user_data = {
            "user_id": f"field_user_{clean_mobile}",
            "name": f"Field User ({clean_mobile})",
            "role": "enumerator",
            "functionary_type": "Field Enumerator",
            "mobile_number": clean_mobile
        }

    token = generate_jwt_token(user_data)
    # Clear stored OTP (but preserve rate-limit window counters)
    if clean_mobile in OTP_STORE:
        OTP_STORE[clean_mobile]["otp"] = None
        OTP_STORE[clean_mobile]["expires_at"] = 0

    return {
        "success": True,
        "token": token,
        "user": user_data
    }

# ---------------------------------------------------------------------------
# Admin login
# ---------------------------------------------------------------------------

def admin_login(username: str, password: str) -> Dict[str, Any]:
    """Authenticate administrator credentials using PBKDF2 verification."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin_users WHERE username = ?", (username,))
    admin = cursor.fetchone()
    conn.close()

    if not admin:
        return {"success": False, "message": "Invalid admin username or password."}

    if not verify_password(password, admin["password_hash"]):
        return {"success": False, "message": "Invalid admin username or password."}

    user_data = {
        "user_id": f"admin_{admin['id']}",
        "username": admin["username"],
        "name": admin["full_name"] or "Census System Admin",
        "role": "admin",
        "functionary_type": "System Administrator"
    }

    token = generate_jwt_token(user_data)
    return {
        "success": True,
        "token": token,
        "user": user_data
    }
