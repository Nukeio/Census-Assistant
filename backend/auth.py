"""
Census Assistant - Authentication & Authorization Layer
Handles Guest Access, OTP Mobile Verification for Field Functionaries, and Admin Login with JWT Tokens.
"""

import os
import time
import hashlib
import random
import logging
from typing import Dict, Any, Optional
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

# In-memory OTP store: mobile -> {otp, expires_at}
OTP_STORE: Dict[str, Dict[str, Any]] = {}

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

def request_otp(mobile_number: str) -> Dict[str, Any]:
    """Generate and send 6-digit OTP for a mobile number."""
    # Clean mobile number
    clean_mobile = "".join([c for c in mobile_number if c.isdigit()])
    if len(clean_mobile) > 10:
        clean_mobile = clean_mobile[-10:]

    if len(clean_mobile) < 10:
        return {"success": False, "message": "Please enter a valid 10-digit mobile number."}

    # Generate 6-digit OTP (e.g. 123456 or random)
    # For testing and demo convenience, default OTP is set or standard
    otp_code = str(random.randint(100000, 999999))
    # If using test user, default to easy OTP or actual generated code
    OTP_STORE[clean_mobile] = {
        "otp": otp_code,
        "expires_at": time.time() + 600 # 10 mins
    }

    logger.info(f"[OTP SEND] Generated OTP for {clean_mobile}: {otp_code}")

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
        # Verified mobile number guest user
        user_data = {
            "user_id": f"field_user_{clean_mobile}",
            "name": f"Field User ({clean_mobile})",
            "role": "enumerator",
            "functionary_type": "Field Enumerator",
            "mobile_number": clean_mobile
        }

    token = generate_jwt_token(user_data)
    # Clear stored OTP
    if clean_mobile in OTP_STORE:
        del OTP_STORE[clean_mobile]

    return {
        "success": True,
        "token": token,
        "user": user_data
    }

def admin_login(username: str, password: str) -> Dict[str, Any]:
    """Authenticate administrator credentials."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin_users WHERE username = ?", (username,))
    admin = cursor.fetchone()
    conn.close()

    if not admin:
        return {"success": False, "message": "Invalid admin username or password."}

    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    if admin["password_hash"] != pwd_hash:
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
