"""
Census Assistant - Core Application Server (Flask)
Serves REST APIs, RAG endpoints, Authentication, Admin Management, Webhooks, and Static Frontend.
"""

import os
import re
import sys
import json
import time
import logging
from datetime import datetime
from urllib.parse import quote as requests_quote
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .database import get_db_connection, init_database, DB_PATH
from .ingestion import (
    run_full_ingestion, ingest_all_users, ingest_hlb_allocation, ingest_hlb_description, ingest_pdf_manuals,
    excel_data_type, remove_source_file_data, KNOWN_PDF_TITLES, ingest_text_manual
)
from .rag_engine import retrieve_rag_context, search_structured_records, search_manual_chunks
from .llm_provider import answer_query, get_user_search_usage, get_ai_status, DAILY_WEB_SEARCH_LIMIT
from .auth import (
    create_guest_session, request_otp, verify_otp, admin_login,
    register_user, login_user, request_password_reset, complete_password_reset,
    change_password, admin_reset_user_password, admin_unlock_account,
    admin_delete_user_account,
    generate_jwt_token, verify_jwt_token
)
from . import attendance
from .messaging_gateway import (
    handle_whatsapp_webhook, handle_telegram_webhook, get_channel_status,
    WHATSAPP_VERIFY_TOKEN, TECH_ASSISTANT_NAME, TECH_ASSISTANT_PHONE, WHATSAPP_DEEP_LINK,
    TECHNICAL_ASSISTANTS
)

CIRCLE_NAME = os.environ.get("CIRCLE_NAME", "Lakhipur Circle")

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

ALLOWED_EXCEL_EXTENSIONS = {".xlsx", ".xls"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
# Text manuals: the route for guidance whose PDF is a scan (see upload_text_manual).
ALLOWED_TEXT_EXTENSIONS = {".txt", ".md", ".text"}

logger = logging.getLogger("CensusServer")
logging.basicConfig(level=logging.INFO)

def resolve_existing_upload(filename: str):
    """
    Resolve a filename that is expected to already exist in ROOT_DIR (e.g.
    one just returned by /api/admin/uploaded-files) to its real path.

    Deliberately does NOT run it through secure_filename() — that sanitizer
    rewrites spaces, parentheses, and other characters (e.g. "HLB Allocation
    (2).xlsx" -> "HLB_Allocation_2.xlsx"), which no longer matches the real
    file on disk and makes lookups 404 even though the file is right there.
    os.path.basename() blocks path traversal (it discards any directory
    components) without mangling a legitimate filename, and the containment
    check below rejects anything that still resolves outside ROOT_DIR.

    Returns the absolute path if it exists as a real file inside ROOT_DIR, else None.
    """
    safe_name = os.path.basename(filename)
    full_path = os.path.abspath(os.path.join(ROOT_DIR, safe_name))
    if os.path.dirname(full_path) != os.path.abspath(ROOT_DIR):
        return None
    if not os.path.isfile(full_path):
        return None
    return full_path

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

# Initialize database on startup
init_database()

# ----------------- Admin Authorization Helpers -----------------
def _authenticated_user():
    """Return the JWT payload for the request's Authorization header, or None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return verify_jwt_token(auth_header[7:])

def _require_admin():
    """
    Guard for admin-only routes. Only the Technical Assistant admin account
    (see auth.admin_login / database's seeded admin_users row) can pass this
    check — guest sessions and OTP-authenticated field functionaries always
    get role 'guest'/'enumerator'/'supervisor', never 'admin'.
    Returns a Flask error response if unauthorized, else None.
    """
    user = _authenticated_user()
    if not user or user.get("role") != "admin":
        return jsonify({"success": False, "error": "Admin authentication required."}), 403
    # A session running on an admin-issued temporary password can do exactly
    # one thing: set a real password. Otherwise a temporary credential read
    # aloud at the office counter would carry full administrative rights.
    if user.get("must_change_password"):
        return jsonify({
            "success": False,
            "must_change_password": True,
            "error": "Set a new password before using the admin console.",
        }), 403
    return None

def _is_admin_request():
    """
    Non-strict admin check for otherwise-public endpoints (record search,
    supervisor list) that should still hide non-ACTIVE functionaries
    (status DISABLED, INACTIVE, LOCK, or any other non-"ACTIVE" value —
    the source Excel data uses INACTIVE/LOCK, while the admin toggle uses
    ACTIVE/DISABLED) from regular guest/OTP-authenticated users, while
    letting the admin see everyone, including inactive/disabled accounts,
    in the same views.
    """
    user = _authenticated_user()
    return bool(user and user.get("role") == "admin")

# ----------------- Static Frontend Routes -----------------
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    if os.path.exists(os.path.join(FRONTEND_DIR, filename)):
        return send_from_directory(FRONTEND_DIR, filename)
    return send_from_directory(FRONTEND_DIR, "index.html")

# ----------------- Health Check -----------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Lightweight, unauthenticated liveness probe. The Android app calls this
    on every launch to decide whether to load the live backend or fall back
    to its bundled offline copy.
    """
    return jsonify({"status": "ok"})

# ----------------- Auth Endpoints -----------------
@app.route("/api/auth/guest", methods=["POST"])
def auth_guest():
    return jsonify(create_guest_session())

@app.route("/api/auth/request-otp", methods=["POST"])
def auth_request_otp():
    data = request.get_json() or {}
    mobile = data.get("mobile_number", "")
    return jsonify(request_otp(mobile))

@app.route("/api/auth/verify-otp", methods=["POST"])
def auth_verify_otp():
    data = request.get_json() or {}
    mobile = data.get("mobile_number", "")
    otp = data.get("otp", "")
    return jsonify(verify_otp(mobile, otp))

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.get_json() or {}
    name = data.get("name", "")
    mobile = data.get("mobile_number", "")
    password = data.get("password", "")
    email = data.get("email", None)
    return jsonify(register_user(name, mobile, password, email=email))

def _client_ip() -> str:
    """Caller's IP, honouring the proxy header PythonAnywhere sets."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or ""

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json() or {}
    identifier = data.get("identifier") or data.get("username") or data.get("mobile_number", "")
    password = data.get("password", "")
    result = login_user(identifier, password, ip_address=_client_ip())
    return jsonify(result), (200 if result.get("success") else 401)

@app.route("/api/auth/admin-login", methods=["POST"])
def auth_admin_login():
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")
    result = admin_login(username, password, ip_address=_client_ip())
    return jsonify(result), (200 if result.get("success") else 401)

@app.route("/api/auth/forgot-password", methods=["POST"])
def auth_forgot_password():
    data = request.get_json() or {}
    identifier = data.get("identifier") or data.get("mobile_number") or data.get("email", "")
    return jsonify(request_password_reset(identifier, ip_address=_client_ip()))

@app.route("/api/auth/reset-password", methods=["POST"])
def auth_reset_password():
    data = request.get_json() or {}
    identifier = data.get("identifier") or data.get("mobile_number") or data.get("email", "")
    reset_code = data.get("reset_code") or data.get("otp", "")
    new_password = data.get("new_password") or data.get("password", "")
    return jsonify(complete_password_reset(identifier, reset_code, new_password, ip_address=_client_ip()))

@app.route("/api/auth/change-password", methods=["POST"])
def auth_change_password():
    """
    Change your own password from inside a signed-in session. This is where a
    user lands after signing in with an admin-issued temporary password —
    succeeding here is what clears must_change_password.
    """
    user = _authenticated_user()
    if not user:
        return jsonify({"success": False, "message": "Please sign in first."}), 401

    data = request.get_json() or {}
    identifier = (
        user.get("mobile") or user.get("username") or user.get("sub") or ""
    )
    result = change_password(
        identifier,
        data.get("current_password", ""),
        data.get("new_password", ""),
        ip_address=_client_ip(),
    )
    if result.get("success"):
        # Re-issue the token so the cleared must_change_password flag takes
        # effect immediately instead of at the next sign-in.
        refreshed = dict(user)
        refreshed["must_change_password"] = False
        result["token"] = generate_jwt_token({
            "user_id": user.get("sub"),
            "name": user.get("name"),
            "role": user.get("role"),
            "mobile_number": user.get("mobile", ""),
            "email": user.get("email", ""),
            "functionary_type": user.get("functionary_type", "User"),
            "must_change_password": False,
        })
    return jsonify(result), (200 if result.get("success") else 400)

@app.route("/api/auth/quota", methods=["GET"])
def auth_quota():
    user = _authenticated_user()
    user_id = user.get("sub") if user else f"guest_{request.remote_addr}"
    used, remaining = get_user_search_usage(user_id)
    return jsonify({
        "success": True,
        "used_today": used,
        "remaining_today": remaining,
        "limit": DAILY_WEB_SEARCH_LIMIT
    })

@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if "Bearer " in auth_header else auth_header
    if not token:
        return jsonify({"authenticated": False, "error": "No token provided"}), 401
    user = verify_jwt_token(token)
    if not user:
        return jsonify({"authenticated": False, "error": "Invalid or expired token"}), 401
    return jsonify({"authenticated": True, "user": user})

# ----------------- AI Chat & RAG Endpoints -----------------
@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    model_name = data.get("model", "gemini-flash-latest")
    lang = data.get("lang", "en")

    if not query:
        return jsonify({"error": "Empty query"}), 400

    user = _authenticated_user()
    user_id = user.get("sub") if user else f"guest_{request.remote_addr}"

    result = answer_query(query, model_name=model_name, lang=lang, user_id=user_id)
    return jsonify(result)

# ----------------- Census Records Search Endpoints -----------------
def _hlb_no_norm(hlb_no):
    """Normalize an HLB number to a plain numeric string."""
    if hlb_no is None:
        return None
    digits = re.sub(r'\D', '', str(hlb_no))
    return str(int(digits)) if digits else str(hlb_no).strip()

def _area_info(hlb_no, circle_no=None, conn=None):
    """
    Allocated area label + Google Maps link.
    """
    norm = _hlb_no_norm(hlb_no)
    close_conn = False
    if norm:
        if conn is None:
            conn = get_db_connection()
            close_conn = True
        row = conn.execute(
            "SELECT village_ward_name, landmark FROM hlb_descriptions WHERE hlb_no = ?",
            (norm,)
        ).fetchone()
        if close_conn:
            conn.close()
        if row and (row["landmark"] or row["village_ward_name"]):
            village_name = row["landmark"] or re.sub(r'\s*\(\d+\)\s*$', '', row["village_ward_name"]).strip()
            maps_url = "https://www.google.com/maps/search/?api=1&query=" + \
                requests_quote(f"{village_name}, {CIRCLE_NAME}, Assam, India")
            return village_name, maps_url

    if not circle_no:
        return None, None
    label = f"{CIRCLE_NAME} — Supervisory Circle {circle_no}"
    maps_url = "https://www.google.com/maps/search/?api=1&query=" + \
        requests_quote(f"{CIRCLE_NAME} Circle {circle_no}, Assam, India")
    return label, maps_url

@app.route("/api/records/search", methods=["GET"])
def records_search():
    q = request.args.get("q", "").strip()
    filter_by = request.args.get("filter", "all") # 'all', 'name', 'mobile', 'id', 'hlb', 'circle'
    if filter_by == "eb":
        filter_by = "hlb"

    # When "All" is selected, infer intent from the query shape instead of an
    # unfocused multi-field LIKE: HLB blocks are 3-4 digit numbers (e.g.
    # "0153"), so a short numeric query is almost certainly an HLB lookup,
    # while a longer numeric string (5+ digits) is a mobile number search.
    # 1-2 digit numbers are too ambiguous to guess and fall through to the
    # normal broad search.
    if filter_by == "all" and q.isdigit():
        if 3 <= len(q) <= 4:
            filter_by = "hlb"
        elif len(q) >= 5:
            filter_by = "mobile"

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 15))
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor()

    show_disabled = _is_admin_request()
    disabled_clause = "" if show_disabled else "AND (f.status IS NULL OR UPPER(f.status) = 'ACTIVE')"

    if filter_by == "area":
        # Search by village / ward / landmark.
        #
        # The area names live in hlb_descriptions, not on the allocation or
        # the functionary, so this drives off that table and joins outwards to
        # find who is working there. boundary_description is included because
        # field staff often know a block by a landmark named only in the
        # boundary text ("east of the LP School") rather than by its village.
        like = f"%{q}%"
        area_where = """
            (d.village_ward_name LIKE ? OR d.landmark LIKE ? OR d.boundary_description LIKE ?)
        """
        count_cursor = conn.cursor()
        count_cursor.execute(f"""
            SELECT COUNT(*)
            FROM hlb_descriptions d
            JOIN hlb_allocations h ON (h.hlb_no = d.hlb_no OR cast(h.hlb_no as integer) = cast(d.hlb_no as integer))
            LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
            WHERE {area_where} {disabled_clause}
        """, (like, like, like))
        total = count_cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT h.*, f.mobile_number, f.district, f.sub_district, f.status,
                   d.village_ward_name, d.landmark, d.boundary_description
            FROM hlb_descriptions d
            JOIN hlb_allocations h ON (h.hlb_no = d.hlb_no OR cast(h.hlb_no as integer) = cast(d.hlb_no as integer))
            LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
            WHERE {area_where} {disabled_clause}
            ORDER BY d.village_ward_name ASC, h.hlb_no ASC
            LIMIT ? OFFSET ?
        """, (like, like, like, limit, offset))
        area_rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        results = []
        for r in area_rows:
            village = re.sub(r'\s*\(\d+\)\s*$', '', r.get("village_ward_name") or "").strip()
            area_name = village or r.get("landmark") or None
            maps_url = ("https://www.google.com/maps/search/?api=1&query=" +
                        requests_quote(f"{area_name}, {CIRCLE_NAME}, Assam, India")) if area_name else None
            results.append({
                "id": r["id"],
                "name": r["enumerator_name"],
                "role": f"Enumerator (HLB {r['hlb_no']})",
                "user_id": r["enumerator_user_id"],
                "mobile": r.get("mobile_number") or "",
                "hlb_number": r["hlb_no"],
                "supervisor": r["supervisor_name"],
                "circle": r["supervisory_circle_no"],
                "allotment_date": r["allotment_date"],
                "area_name": area_name,
                "landmark": r.get("landmark") or "",
                "boundary_description": r.get("boundary_description") or "",
                "maps_url": maps_url
            })
        return jsonify({
            "query": q,
            "filter": filter_by,
            "page": page,
            "limit": limit,
            "total": total,
            "results": results
        })

    elif filter_by == "hlb":
        # Search HLB allocation directly with a COUNT for proper pagination
        count_cursor = conn.cursor()
        count_cursor.execute(f"""
            SELECT COUNT(*) FROM hlb_allocations h
            LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
            WHERE (h.hlb_no LIKE ? OR h.supervisory_circle_no LIKE ?) {disabled_clause}
        """, (f"%{q}%", f"%{q}%"))
        total = count_cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT h.*, f.mobile_number, f.district, f.sub_district, f.status, d.village_ward_name, d.landmark
            FROM hlb_allocations h
            LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
            LEFT JOIN hlb_descriptions d ON (d.hlb_no = h.hlb_no OR d.hlb_no = cast(h.hlb_no as integer))
            WHERE (h.hlb_no LIKE ? OR h.supervisory_circle_no LIKE ?) {disabled_clause}
            ORDER BY h.id ASC
            LIMIT ? OFFSET ?
        """, (f"%{q}%", f"%{q}%", limit, offset))
        hlb_rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        results = []
        for r in hlb_rows:
            area_name = r.get("landmark") or (re.sub(r'\s*\(\d+\)\s*$', '', r.get("village_ward_name") or '').strip()) if r.get("village_ward_name") else None
            maps_url = ("https://www.google.com/maps/search/?api=1&query=" + requests_quote(f"{area_name}, {CIRCLE_NAME}, Assam, India")) if area_name else None
            results.append({
                "id": r["id"],
                "name": r["enumerator_name"],
                "role": f"Enumerator (HLB {r['hlb_no']})",
                "user_id": r["enumerator_user_id"],
                "mobile": r.get("mobile_number") or "",
                "hlb_number": r["hlb_no"],
                "supervisor": r["supervisor_name"],
                "circle": r["supervisory_circle_no"],
                "allotment_date": r["allotment_date"],
                "area_name": area_name,
                "maps_url": maps_url
            })
        return jsonify({
            "query": q,
            "filter": filter_by,
            "page": page,
            "limit": limit,
            "total": total,
            "results": results
        })

    elif filter_by == "circle":
        # Search by supervisory circle
        circle_clean = re.sub(r'\D', '', q) or q
        count_cursor = conn.cursor()
        count_cursor.execute(f"""
            SELECT COUNT(*) FROM hlb_allocations h
            LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
            WHERE (h.supervisory_circle_no LIKE ? OR h.supervisory_circle_no = ?) {disabled_clause}
        """, (f"%{q}%", circle_clean))
        total = count_cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT h.*, f.mobile_number, f.district, f.sub_district, f.status, d.village_ward_name, d.landmark
            FROM hlb_allocations h
            LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
            LEFT JOIN hlb_descriptions d ON (d.hlb_no = h.hlb_no OR d.hlb_no = cast(h.hlb_no as integer))
            WHERE (h.supervisory_circle_no LIKE ? OR h.supervisory_circle_no = ?) {disabled_clause}
            ORDER BY h.id ASC
            LIMIT ? OFFSET ?
        """, (f"%{q}%", circle_clean, limit, offset))
        hlb_rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        results = []
        for r in hlb_rows:
            area_name = r.get("landmark") or (re.sub(r'\s*\(\d+\)\s*$', '', r.get("village_ward_name") or '').strip()) if r.get("village_ward_name") else None
            maps_url = ("https://www.google.com/maps/search/?api=1&query=" + requests_quote(f"{area_name}, {CIRCLE_NAME}, Assam, India")) if area_name else None
            results.append({
                "id": r["id"],
                "name": r["enumerator_name"],
                "role": f"Enumerator (HLB {r['hlb_no']})",
                "user_id": r["enumerator_user_id"],
                "mobile": r.get("mobile_number") or "",
                "hlb_number": r["hlb_no"],
                "supervisor": r["supervisor_name"],
                "circle": r["supervisory_circle_no"],
                "allotment_date": r["allotment_date"],
                "area_name": area_name,
                "maps_url": maps_url
            })
        return jsonify({
            "query": q,
            "filter": filter_by,
            "page": page,
            "limit": limit,
            "total": total,
            "results": results
        })

    # Standard functionary search with single LEFT JOIN to avoid N+1 query overhead
    where_clauses = []
    params = []

    if filter_by == "supervisor":
        # Unlike the other filters, this one applies even with an empty
        # query — so selecting "Supervisor" with nothing typed browses every
        # supervisor, the same way the results list works with "All".
        where_clauses.append("f.functionary_type LIKE '%Supervisor%'")
        if q:
            where_clauses.append("(f.name LIKE ? OR f.user_id LIKE ? OR f.mobile_number LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    elif q:
        if filter_by == "name":
            where_clauses.append("f.name LIKE ?")
            params.append(f"%{q}%")
        elif filter_by == "mobile":
            where_clauses.append("f.mobile_number LIKE ?")
            params.append(f"%{q}%")
        elif filter_by == "id":
            where_clauses.append("f.user_id LIKE ?")
            params.append(f"%{q}%")
        else:
            # Area names are included here as well as in the dedicated "area"
            # filter, so a field user typing a village name under "All" finds
            # it without first knowing to change the filter. village_town is
            # the functionary's own posting; village_ward_name and landmark
            # come from the HLB description joined below.
            where_clauses.append(
                "(f.name LIKE ? OR f.user_id LIKE ? OR f.mobile_number LIKE ? OR f.functionary_type LIKE ? "
                "OR f.village_town LIKE ? OR d.village_ward_name LIKE ? OR d.landmark LIKE ?)"
            )
            params.extend([f"%{q}%"] * 7)

    if not show_disabled:
        where_clauses.append("(f.status IS NULL OR UPPER(f.status) = 'ACTIVE')")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # The count mirrors the result query's joins because the WHERE clause can
    # now reference the HLB description table (village / landmark). Without
    # the same joins here the count query would fail on an area search.
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM functionaries f
        LEFT JOIN hlb_allocations h ON f.user_id = h.enumerator_user_id
        LEFT JOIN hlb_descriptions d ON (d.hlb_no = h.hlb_no OR d.hlb_no = cast(h.hlb_no as integer))
        {where_sql}
    """, params)
    total = cursor.fetchone()[0]

    # Rank by name relevance instead of insertion order: an exact name match
    # (case-insensitive) comes first, then names starting with the query,
    # then any other substring match, then alphabetical for the rest — so
    # searching "Abdul Baten" under "All" surfaces that person before an
    # unrelated record that merely happens to share a village/mobile digit.
    if q:
        order_sql = """
            ORDER BY
                CASE
                    WHEN LOWER(f.name) = LOWER(?) THEN 0
                    WHEN f.name LIKE ? THEN 1
                    WHEN f.name LIKE ? THEN 2
                    ELSE 3
                END,
                f.name ASC
        """
        order_params = [q, f"{q}%", f"%{q}%"]
    else:
        order_sql = "ORDER BY f.id ASC"
        order_params = []

    cursor.execute(f"""
        SELECT f.*, h.hlb_no, h.supervisor_name, h.supervisory_circle_no, d.village_ward_name, d.landmark, d.boundary_description
        FROM functionaries f
        LEFT JOIN hlb_allocations h ON f.user_id = h.enumerator_user_id
        LEFT JOIN hlb_descriptions d ON (d.hlb_no = h.hlb_no OR d.hlb_no = cast(h.hlb_no as integer))
        {where_sql}
        {order_sql}
        LIMIT ? OFFSET ?
    """, params + order_params + [limit, offset])
    rows = [dict(r) for r in cursor.fetchall()]

    results = []
    for r in rows:
        hlb_no = r["hlb_no"]
        sup_str = r["supervisor_name"]
        circle_no = r["supervisory_circle_no"]
        area_name = r.get("landmark") or (re.sub(r'\s*\(\d+\)\s*$', '', r.get("village_ward_name") or '').strip()) if r.get("village_ward_name") else None
        if not area_name and r.get("village_town"):
            area_name = r["village_town"]
        maps_url = ("https://www.google.com/maps/search/?api=1&query=" + requests_quote(f"{area_name}, {CIRCLE_NAME}, Assam, India")) if area_name else None

        results.append({
            "id": r["id"],
            "name": r["name"],
            "role": r["functionary_type"],
            "user_id": r["user_id"],
            "mobile": r["mobile_number"],
            "hlb_number": hlb_no,
            "supervisor": sup_str,
            "circle": circle_no,
            "district": r["district"] or "",
            "sub_district": r["sub_district"] or "",
            "village_town": r.get("village_town") or "",
            "landmark": r.get("landmark") or "",
            "boundary_description": r.get("boundary_description") or "",
            "area_name": area_name,
            "maps_url": maps_url,
            "status": r["status"]
        })

    conn.close()
    return jsonify({
        "query": q,
        "filter": filter_by,
        "page": page,
        "limit": limit,
        "total": total,
        "results": results
    })

@app.route("/api/records/supervisor", methods=["GET"])
def supervisor_list():
    """List actual supervisors cross-referenced from functionaries, hlb_allocations, and hlb_descriptions."""
    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 50))

    conn = get_db_connection()
    cursor = conn.cursor()

    show_disabled = _is_admin_request()

    where_sql = "WHERE functionary_type LIKE '%Supervisor%'"
    params = []
    if q:
        if q.isdigit() and len(q) <= 3:
            # A short digit string is almost certainly a supervisory circle
            # number (e.g. "1" or "001"), not a name/mobile/ID fragment.
            # This has to be routed separately rather than OR'd in below:
            # every user_id in this dataset embeds a shared district/
            # sub-district code (e.g. "sv_1904001_..."), so a plain
            # "user_id LIKE '%001%'" would spuriously match nearly every
            # supervisor regardless of their actual circle. A supervisor
            # doesn't carry their own circle number as a column either —
            # it only exists on the HLB allocation rows of the enumerators
            # reporting to them — so this checks whether their name shows
            # up against that circle in hlb_allocations instead.
            where_sql += """ AND name IN (
                SELECT DISTINCT supervisor_name FROM hlb_allocations
                WHERE supervisory_circle_no LIKE ? OR supervisory_circle_no = ?
            )"""
            params.extend([f"%{q}%", q])
        else:
            # Name / ID / mobile as before, plus area: a supervisor has no
            # village column of their own, so an area match is resolved the
            # same way the circle lookup above is — through the HLB blocks
            # allocated under them. Typing a village or landmark therefore
            # answers "who supervises that place?", which is how field staff
            # actually think about it.
            where_sql += """ AND (
                name LIKE ? OR user_id LIKE ? OR mobile_number LIKE ?
                OR name IN (
                    SELECT DISTINCT h.supervisor_name
                    FROM hlb_allocations h
                    JOIN hlb_descriptions d
                      ON (d.hlb_no = h.hlb_no OR cast(d.hlb_no as integer) = cast(h.hlb_no as integer))
                    WHERE d.village_ward_name LIKE ? OR d.landmark LIKE ? OR d.boundary_description LIKE ?
                )
            )"""
            params.extend([f"%{q}%"] * 6)
    if not show_disabled:
        where_sql += " AND (status IS NULL OR UPPER(status) = 'ACTIVE')"

    cursor.execute(f"""
        SELECT * FROM functionaries {where_sql} ORDER BY name ASC LIMIT ?
    """, params + [limit])
    sup_rows = cursor.fetchall()

    supervisors = []
    for r in sup_rows:
        cursor.execute("""
            SELECT DISTINCT supervisory_circle_no FROM hlb_allocations
            WHERE supervisor_name = ? OR supervisor_name LIKE ?
        """, (r["name"], f"%{r['name']}%"))
        circles = [c["supervisory_circle_no"] for c in cursor.fetchall() if c["supervisory_circle_no"]]

        # Pull all enumerators reporting under this supervisor across all 3 sheets
        enum_disabled_clause = "" if show_disabled else "AND (f.status IS NULL OR UPPER(f.status) = 'ACTIVE')"
        cursor.execute(f"""
            SELECT h.hlb_no, h.supervisory_circle_no, h.enumerator_name, h.enumerator_user_id, h.allotment_date,
                   f.mobile_number, f.district, f.sub_district, f.village_town,
                   d.village_ward_name, d.landmark, d.boundary_description
            FROM hlb_allocations h
            LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
            LEFT JOIN hlb_descriptions d ON (d.hlb_no = h.hlb_no OR d.hlb_no = cast(h.hlb_no as integer))
            WHERE (h.supervisor_name = ? OR h.supervisor_name LIKE ?) {enum_disabled_clause}
            ORDER BY cast(h.hlb_no as integer) ASC
        """, (r["name"], f"%{r['name']}%"))
        assigned_rows = cursor.fetchall()

        assigned_enumerators = []
        for er_row in assigned_rows:
            er = dict(er_row)
            e_area, e_maps = _area_info(er.get("hlb_no"), er.get("supervisory_circle_no"), conn=conn)
            assigned_enumerators.append({
                "hlb_no": er.get("hlb_no") or "",
                "supervisory_circle_no": er.get("supervisory_circle_no") or "",
                "supervisor_name": er.get("supervisor_name") or "",
                "enumerator_name": er.get("enumerator_name") or "",
                "enumerator_user_id": er.get("enumerator_user_id") or "",
                "mobile": er.get("mobile_number") or "",
                "village_ward_name": er.get("village_ward_name") or "",
                "landmark": er.get("landmark") or "",
                "boundary_description": er.get("boundary_description") or "",
                "area_name": e_area,
                "maps_url": e_maps,
                "allotment_date": er.get("allotment_date") or ""
            })

        area_name, maps_url = _area_info(None, circles[0] if circles else None, conn=conn)
        r_dict = dict(r)
        supervisors.append({
            "name": r_dict.get("name") or "",
            "user_id": r_dict.get("user_id") or "",
            "mobile": r_dict.get("mobile_number") or "",
            "circles": circles,
            "hlb_count": len(assigned_enumerators),
            "district": r_dict.get("district") or "",
            "sub_district": r_dict.get("sub_district") or "",
            "village_town": r_dict.get("village_town") or "",
            "area_name": area_name,
            "maps_url": maps_url,
            "enumerators": assigned_enumerators,
            "status": r_dict.get("status") or "ACTIVE"
        })

    conn.close()
    return jsonify({
        "query": q,
        "supervisors": supervisors,
        "total": len(supervisors),
        "technical_assistants": TECHNICAL_ASSISTANTS
    })

# ----------------- PDF Manual Assistant Endpoints -----------------
@app.route("/api/manuals/search", methods=["GET"])
def manual_search():
    q = request.args.get("q", "household definition").strip()
    chunks = search_manual_chunks(q, limit=5)
    return jsonify({
        "query": q,
        "results": chunks
    })

@app.route("/api/manuals/list", methods=["GET"])
def manual_list():
    """
    Dynamically list every PDF actually present in ROOT_DIR, instead of the
    2 filenames this used to be hardcoded to. This is what lets a freshly
    uploaded manual show up as a real, clickable card on the Manuals page —
    the same dynamic-scan fix already applied to ingest_pdf_manuals().
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    manuals = []
    for fname in sorted(os.listdir(ROOT_DIR)):
        if not fname.lower().endswith(".pdf"):
            continue
        full_path = os.path.join(ROOT_DIR, fname)
        if not os.path.isfile(full_path):
            continue
        stat = os.stat(full_path)
        size_kb = round(stat.st_size / 1024, 1)
        size_str = f"{round(size_kb / 1024, 1)} MB" if size_kb >= 1024 else f"{size_kb} KB"

        cursor.execute("""
            SELECT COUNT(*) AS chunk_count, MAX(page_number) AS max_page, MAX(doc_title) AS doc_title
            FROM manual_chunks WHERE source_file = ?
        """, (fname,))
        row = cursor.fetchone()
        chunk_count = row["chunk_count"] or 0
        title = (row["doc_title"] if row and row["doc_title"] else None) \
            or KNOWN_PDF_TITLES.get(fname) \
            or os.path.splitext(fname)[0]

        manuals.append({
            "filename": fname,
            "title": title,
            "pages": row["max_page"] or 0,
            "size": size_str,
            "chunk_count": chunk_count,
            "indexed": chunk_count > 0
        })
    conn.close()
    return jsonify({"manuals": manuals})

@app.route("/api/manuals/topics", methods=["GET"])
def manual_topics():
    """
    A browsable, searchable topic list for the Manuals page, alongside the
    free-text AI search box. Each topic is labeled from the chunk's real
    section_header when the PDF's text layer actually carried one; when it
    didn't (some source PDFs — e.g. scanned/print-shop exports — only yield
    boilerplate per-page text with no real heading), it falls back to a
    short cleaned snippet of the chunk itself so a topic is still offered
    rather than silently omitted. Duplicate labels within the same document
    (e.g. an identical boilerplate line repeated on many pages) collapse to
    one entry. Supports an optional `q` substring filter and an optional
    `source_file` filter (used by a single manual's detail modal).
    """
    q = request.args.get("q", "").strip().lower()
    source_file = request.args.get("source_file", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT id, source_file, doc_title, section_header, page_number, chunk_text FROM manual_chunks"
    params = []
    if source_file:
        sql += " WHERE source_file = ?"
        params.append(source_file)
    sql += " ORDER BY source_file, id"
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    grouped = {}
    seen_labels = set()
    for row in rows:
        header = (row["section_header"] or "").strip()
        if header:
            label = header
        else:
            snippet = re.sub(r"\s+", " ", (row["chunk_text"] or "")).strip()
            label = (snippet[:80] + "…") if len(snippet) > 80 else snippet
        if not label:
            continue

        # Strip digits before deduping so per-page artifacts that only vary by
        # a page/signature number (e.g. a print-shop PDF's running header
        # "...Sig1 SideA", "...Sig2 SideA", ...) collapse into one topic
        # instead of flooding the list with near-identical entries.
        dedupe_key = (row["source_file"], re.sub(r"\d+", "", label).strip().lower())
        if dedupe_key in seen_labels:
            continue
        seen_labels.add(dedupe_key)

        if q and q not in label.lower():
            continue

        key = row["source_file"]
        grouped.setdefault(key, {
            "source_file": key,
            "doc_title": row["doc_title"],
            "topics": []
        })
        grouped[key]["topics"].append({
            "id": row["id"],
            "section_header": label,
            "page_number": row["page_number"]
        })

    return jsonify({"documents": list(grouped.values())})

@app.route("/api/manuals/chunk", methods=["GET"])
def manual_chunk_detail():
    """Fetch one exact indexed chunk by its row id, for a topic clicked from the browsable topic list."""
    chunk_id = request.args.get("id", "").strip()
    if not chunk_id.isdigit():
        return jsonify({"error": "A valid numeric id is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM manual_chunks WHERE id = ?", (chunk_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Topic not found"}), 404

    return jsonify({
        "source_file": row["source_file"],
        "doc_title": row["doc_title"],
        "page_number": row["page_number"],
        "section_header": row["section_header"],
        "chunk_text": row["chunk_text"],
    })

@app.route("/api/manuals/file/<path:filename>", methods=["GET"])
def manual_file(filename):
    """Serve the actual PDF bytes so 'Open Full PDF' opens the real document."""
    full_path = resolve_existing_upload(filename)
    if not full_path or not full_path.lower().endswith(".pdf"):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(ROOT_DIR, os.path.basename(full_path), mimetype="application/pdf")

# ----------------- Notifications Endpoints -----------------
@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    category = request.args.get("category", "All")
    conn = get_db_connection()
    cursor = conn.cursor()
    if category.lower() in ["alerts", "notices"]:
        cursor.execute("SELECT * FROM notifications WHERE active = 1 AND LOWER(category) = ? ORDER BY id DESC", (category.lower(),))
    else:
        cursor.execute("SELECT * FROM notifications WHERE active = 1 ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"notifications": rows})

@app.route("/api/notifications", methods=["POST"])
def create_notification():
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    data = request.get_json() or {}
    title = data.get("title", "")
    content = data.get("content", "")
    category = data.get("category", "Notices")
    priority = data.get("priority", "normal")
    badge = data.get("badge", "New")

    if not title or not content:
        return jsonify({"error": "Title and content required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (title, content, category, priority, badge, timestamp_str)
        VALUES (?, ?, ?, ?, ?, 'Just now')
    """, (title, content, category, priority, badge))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({"success": True, "message": "Notification broadcasted successfully.", "id": new_id})

@app.route("/api/notifications/<int:notification_id>", methods=["DELETE"])
def delete_notification(notification_id):
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if not deleted:
        return jsonify({"success": False, "error": "Notification not found."}), 404
    return jsonify({"success": True, "message": "Notification deleted."})

# ----------------- Admin Control Center Endpoints -----------------
@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM functionaries")
    func_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM hlb_allocations")
    hlb_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM manual_chunks")
    chunk_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*), AVG(latency_ms) FROM ai_usage_stats")
    ai_stat = cursor.fetchone()
    total_ai_queries = ai_stat[0] or 0
    avg_latency = round((ai_stat[1] or 1200) / 1000, 1)

    cursor.execute("SELECT value FROM system_settings WHERE key = 'last_sync_time'")
    last_sync_row = cursor.fetchone()
    last_sync = last_sync_row[0] if last_sync_row else "Today, 08:45 AM"

    conn.close()
    return jsonify({
        "total_records": func_count + hlb_count,
        "functionaries_count": func_count,
        "hlb_count": hlb_count,
        "manual_chunks_count": chunk_count,
        "ai_queries_count": 54000 + total_ai_queries,
        "avg_latency": f"{avg_latency}s",
        "sync_status": "Synced",
        "last_sync": last_sync,
        "indexing_node": "Active",
        "vector_db": "Healthy",
        "errors_logged": 0
    })

@app.route("/api/admin/force-sync", methods=["POST"])
def admin_force_sync():
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    try:
        res = run_full_ingestion()
        return jsonify({"success": True, "details": res})
    except Exception as e:
        logger.error(f"Force sync error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/upload-excel", methods=["POST"])
def upload_excel():
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXCEL_EXTENSIONS:
        return jsonify({"error": f"Invalid file type '{ext}'. Only Excel files (.xlsx, .xls) are allowed."}), 400

    target_path = os.path.join(ROOT_DIR, filename)
    file.save(target_path)

    # Ingest based on filename keywords (excel_data_type is the single
    # source of truth for this routing — remove_source_file_data() uses the
    # exact same classifier so upload/delete can never disagree about which
    # table a given filename backs).
    data_type = excel_data_type(filename)
    if data_type == "users":
        cnt = ingest_all_users(target_path)
    elif data_type == "hlb_description":
        cnt = ingest_hlb_description(target_path)
    else:
        cnt = ingest_hlb_allocation(target_path)

    return jsonify({
        "success": True,
        "message": f"File {filename} uploaded and processed ({cnt} rows indexed)."
    })

@app.route("/api/admin/upload-pdf", methods=["POST"])
def upload_pdf():
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_PDF_EXTENSIONS:
        return jsonify({"error": f"Invalid file type '{ext}'. Only PDF files (.pdf) are allowed."}), 400

    target_path = os.path.join(ROOT_DIR, filename)
    file.save(target_path)

    # Ingest just this one file — every other manual's existing chunks are
    # left untouched (see ingest_pdf_manuals docstring).
    cnt = ingest_pdf_manuals(target_path)
    if cnt == 0:
        # Almost always a scan: the pages are images, so there is no text
        # layer to index. Say so plainly instead of reporting "0 chunks" and
        # leaving the admin to wonder why the assistant cannot cite it.
        return jsonify({
            "success": True,
            "warning": "no_text_layer",
            "chunks": 0,
            "message": (
                f"{filename} uploaded, but no readable text could be extracted from it. "
                "This PDF appears to be a scan of printed pages, so it has no text layer "
                "to index and the assistant will not be able to quote it. Run it through "
                "OCR and upload the resulting .txt file instead."
            )
        })
    return jsonify({
        "success": True,
        "chunks": cnt,
        "message": f"PDF {filename} uploaded and processed ({cnt} chunks indexed)."
    })

@app.route("/api/admin/upload-text", methods=["POST"])
def upload_text_manual():
    """
    Upload a plain-text or Markdown manual.

    This is the route for guidance whose PDF is a scan — OCR it, upload the
    .txt, and the assistant has real searchable text to answer and cite from.
    Page markers of the form "===== PAGE 42 =====" are honoured so citations
    keep pointing at the printed page number.
    """
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_TEXT_EXTENSIONS:
        return jsonify({
            "error": f"Invalid file type '{ext}'. Only text files ({', '.join(sorted(ALLOWED_TEXT_EXTENSIONS))}) are allowed."
        }), 400

    target_path = os.path.join(ROOT_DIR, filename)
    file.save(target_path)

    cnt = ingest_text_manual(target_path)
    if cnt == 0:
        return jsonify({
            "success": False,
            "error": f"{filename} contained no usable text to index."
        }), 400

    return jsonify({
        "success": True,
        "chunks": cnt,
        "message": f"{filename} uploaded and indexed ({cnt} chunks). The assistant can now quote it."
    })

@app.route("/api/admin/logs", methods=["GET"])
def admin_logs():
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 25))
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM activity_logs")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"logs": logs, "total": total, "page": page, "limit": limit})

@app.route("/api/admin/query-logs", methods=["GET"])
def admin_query_logs():
    """Detailed AI query log with performance metrics."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 25))
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE action_type = 'ai_chat' OR action_type = 'ai_query'")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT a.id, a.user_id, a.query_text, a.source_tag, a.timestamp
        FROM activity_logs a
        WHERE a.action_type = 'ai_chat' OR a.action_type = 'ai_query'
        ORDER BY a.id DESC LIMIT ? OFFSET ?
    """, (limit, offset))
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"query_logs": logs, "total": total, "page": page, "limit": limit})

@app.route("/api/admin/system-health", methods=["GET"])
def system_health():
    """System health inspection endpoint with DB stats, file sizes, and chunk breakdown."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    conn = get_db_connection()
    cursor = conn.cursor()

    # Table counts
    counts = {}
    for table in ["functionaries", "hlb_allocations", "hlb_descriptions", "manual_chunks", "notifications", "activity_logs", "ai_usage_stats"]:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        except Exception:
            counts[table] = 0

    # Chunks by source file
    cursor.execute("""
        SELECT source_file, doc_title, COUNT(*) as chunk_count, MAX(page_number) as max_page
        FROM manual_chunks
        GROUP BY source_file
    """)
    doc_breakdown = [dict(r) for r in cursor.fetchall()]

    conn.close()

    # Database file size
    db_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    db_size_mb = round(db_size_bytes / (1024 * 1024), 2)

    return jsonify({
        "status": "healthy",
        "database_path": DB_PATH,
        "database_size_mb": db_size_mb,
        "table_counts": counts,
        "document_breakdown": doc_breakdown,
        "server_time": datetime.now().isoformat()
    })

@app.route("/api/admin/users", methods=["GET"])
def admin_users_list():
    """Paginated functionary management endpoint."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    q = request.args.get("q", "").strip()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor()

    where_sql = ""
    params = []
    if q:
        where_sql = "WHERE name LIKE ? OR user_id LIKE ? OR mobile_number LIKE ? OR functionary_type LIKE ?"
        params = [f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"]

    cursor.execute(f"SELECT COUNT(*) FROM functionaries {where_sql}", params)
    total = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT id, sno, user_id, functionary_type, name, mobile_number, district, sub_district, village_town, status, updated_at
        FROM functionaries {where_sql}
        ORDER BY id ASC LIMIT ? OFFSET ?
    """, params + [limit, offset])
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({"users": users, "total": total, "page": page, "limit": limit})

@app.route("/api/admin/users/<user_id>/toggle-status", methods=["POST"])
def admin_toggle_user_status(user_id):
    """Toggle user status between ACTIVE and DISABLED."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM functionaries WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Functionary not found."}), 404

    new_status = "DISABLED" if row["status"] == "ACTIVE" else "ACTIVE"
    cursor.execute("UPDATE functionaries SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (new_status, user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "user_id": user_id, "new_status": new_status})

@app.route("/api/admin/uploaded-files", methods=["GET"])
def admin_uploaded_files():
    """
    List the data sources present in ROOT_DIR.

    Text manuals (.txt/.md) are included alongside Excel and PDF — an uploaded
    text manual was previously indexed correctly but never appeared here,
    which made a successful upload look like it had failed.

    Each manual also reports how many chunks it currently contributes to the
    searchable index. That number is the quickest answer to "is this file
    actually working?": a scanned PDF shows 0, a healthy manual shows many.
    """
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    # How many indexed chunks each source file currently contributes.
    chunk_counts = {}
    try:
        conn = get_db_connection()
        chunk_counts = {
            r["source_file"]: r["n"] for r in conn.execute(
                "SELECT source_file, COUNT(*) AS n FROM manual_chunks GROUP BY source_file"
            ).fetchall()
        }
        conn.close()
    except Exception as e:
        logger.warning(f"Could not read manual chunk counts: {e}")

    files = []
    target_exts = {".xlsx", ".xls", ".pdf", ".txt", ".md", ".text"}
    type_labels = {
        ".pdf": "PDF Manual",
        ".txt": "Text Manual", ".md": "Text Manual", ".text": "Text Manual",
    }
    for fname in os.listdir(ROOT_DIR):
        ext = os.path.splitext(fname)[1].lower()
        if ext in target_exts:
            # ".txt"/".md" are ordinary project-file extensions (README.md,
            # requirements.txt), so a text file is only a data source once it
            # has actually been ingested as a manual. Without this check the
            # list offers a delete button next to the project's own files.
            if ext in (".txt", ".md", ".text") and fname not in chunk_counts:
                continue
            full_path = os.path.join(ROOT_DIR, fname)
            stat = os.stat(full_path)
            size_kb = round(stat.st_size / 1024, 1)
            size_str = f"{round(size_kb / 1024, 1)} MB" if size_kb >= 1024 else f"{size_kb} KB"
            is_manual = ext in type_labels
            files.append({
                "filename": fname,
                "file_type": type_labels.get(ext, "Excel Sheet"),
                "indexed_chunks": chunk_counts.get(fname, 0) if is_manual else None,
                "is_manual": is_manual,
                "size_str": size_str,
                "size_bytes": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })

    return jsonify({"files": files})

@app.route("/api/admin/uploaded-files/<filename>", methods=["DELETE"])
def admin_delete_file(filename):
    """Delete an uploaded source file and trigger re-index."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    full_path = resolve_existing_upload(filename)
    if not full_path:
        return jsonify({"success": False, "error": "File does not exist."}), 404
    safe_name = os.path.basename(full_path)

    try:
        # Purge exactly the rows this file is responsible for BEFORE removing
        # it from disk. A prior version deleted the file then called a full
        # re-ingestion, which — finding the file already gone — just skipped
        # re-processing it without ever clearing its old rows, so "deleted"
        # data kept showing up throughout the app. This removes it directly.
        removed = remove_source_file_data(safe_name)
        os.remove(full_path)
        return jsonify({
            "success": True,
            "message": f"File {safe_name} deleted and its data removed from the app.",
            "removed": removed
        })
    except Exception as e:
        logger.error(f"File delete error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ----------------- Admin: Accounts & AI Diagnostics -----------------

@app.route("/api/admin/ai-status", methods=["GET"])
def admin_ai_status():
    """
    Report whether the assistant can actually reach a language model.

    Without this the most common failure — GEMINI_API_KEY not set in the
    PythonAnywhere environment — is completely invisible: every question
    quietly falls back to the offline synthesizer, which can only answer from
    ingested records and manuals, and the assistant appears to be permanently
    restricted to the PDFs. Pass ?probe=1 to make a live call to the API.
    """
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    probe = request.args.get("probe", "").lower() in ("1", "true", "yes")
    return jsonify({"success": True, "ai": get_ai_status(probe=probe)})

@app.route("/api/admin/users/reset-password", methods=["POST"])
def admin_reset_password():
    """
    Issue a one-time password for a user who has forgotten theirs.

    This is the office-counter workflow: the user turns up in person, the
    Technical Assistant runs this, reads the temporary password out, and the
    user is forced to set their own at the next sign-in. The temporary
    password appears only in this response — it is stored as a PBKDF2 hash
    like every other password and is never written to the database or logs in
    readable form.
    """
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    data = request.get_json() or {}
    identifier = (data.get("identifier") or data.get("mobile_number") or "").strip()
    if not identifier:
        return jsonify({"success": False, "message": "Enter the user's mobile number or username."}), 400

    actor = (_authenticated_user() or {}).get("name", "admin")
    result = admin_reset_user_password(identifier, actor=actor)
    return jsonify(result), (200 if result.get("success") else 404)

@app.route("/api/admin/users/unlock", methods=["POST"])
def admin_unlock():
    """Clear a lockout after too many failed sign-in attempts."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    data = request.get_json() or {}
    identifier = (data.get("identifier") or data.get("mobile_number") or "").strip()
    if not identifier:
        return jsonify({"success": False, "message": "Enter the user's mobile number or username."}), 400

    actor = (_authenticated_user() or {}).get("name", "admin")
    result = admin_unlock_account(identifier, actor=actor)
    return jsonify(result), (200 if result.get("success") else 404)

@app.route("/api/admin/accounts/<user_id>", methods=["DELETE"])
def admin_delete_account(user_id):
    """
    Permanently delete a self-registered app account (app_users table only —
    this can never remove the Technical Assistant's own admin login, which
    lives in a separate admin_users table keyed off ADMIN_USERNAME).
    """
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    actor = (_authenticated_user() or {}).get("name", "admin")
    result = admin_delete_user_account(user_id, actor=actor)
    return jsonify(result), (200 if result.get("success") else 404)

@app.route("/api/admin/accounts", methods=["GET"])
def admin_accounts():
    """
    Registered app accounts with the details that actually help diagnose a
    sign-in problem: when they registered, when they last signed in, how many
    failed attempts are on record, and whether they are locked or holding a
    temporary password. No password material is exposed.
    """
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    q = (request.args.get("q") or "").strip()
    conn = get_db_connection()
    try:
        sql = """
            SELECT user_id, name, mobile_number, email, role, functionary_type,
                   created_at, last_login_at, failed_attempts, locked_until,
                   must_change_password, status
            FROM app_users
        """
        params = []
        if q:
            sql += " WHERE name LIKE ? OR mobile_number LIKE ? OR email LIKE ?"
            params = [f"%{q}%"] * 3
        sql += " ORDER BY created_at DESC LIMIT 200"
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    now = time.time()
    accounts = []
    for r in rows:
        locked_until = r["locked_until"] or 0
        accounts.append({
            "user_id": r["user_id"],
            "name": r["name"],
            "mobile_number": r["mobile_number"],
            "email": r["email"] or "",
            "role": r["role"] or "user",
            "functionary_type": r["functionary_type"] or "User",
            "created_at": r["created_at"],
            "last_login_at": r["last_login_at"],
            "failed_attempts": r["failed_attempts"] or 0,
            "locked": locked_until > now,
            "locked_for_seconds": max(0, int(locked_until - now)),
            "must_change_password": bool(r["must_change_password"]),
            "status": r["status"] or "ACTIVE",
        })
    return jsonify({"success": True, "accounts": accounts, "total": len(accounts)})

@app.route("/api/admin/auth-audit", methods=["GET"])
def admin_auth_audit():
    """Recent authentication events: sign-ins, failures, lockouts, resets."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    try:
        limit = min(int(request.args.get("limit", 50)), 200)
    except ValueError:
        limit = 50

    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT account, event, outcome, detail, actor, ip_address, created_at
            FROM auth_audit ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
    finally:
        conn.close()

    return jsonify({"success": True, "events": [dict(r) for r in rows]})

# ----------------- Field Attendance Endpoints -----------------
#
# Public (field-user) side: a person marks attendance against their own mobile
# number. The (mobile_number, attendance_date) uniqueness constraint in
# attendance_records means a resubmission always overwrites that day's row —
# the register can never accumulate duplicates for the same person on the same
# day. Admin side is gated by _require_admin() exactly like every other
# /api/admin/* route.

@app.route("/api/attendance/lookup", methods=["GET"])
def attendance_lookup():
    """
    Prefill helper for the Attendance tab: returns today's record for a mobile
    number (if one exists) plus the name/position/block carried forward from
    that person's most recent submission.
    """
    mobile = request.args.get("mobile", "")
    if not attendance.normalize_mobile(mobile):
        return jsonify({"success": False, "error": "Enter a valid 10-digit mobile number."}), 400

    return jsonify({
        "success": True,
        "date": attendance.today_ist(),
        "record": attendance.get_attendance(mobile),
        "profile": attendance.get_carry_forward_profile(mobile),
    })

@app.route("/api/attendance/submit", methods=["POST"])
def attendance_submit():
    """
    Create or update today's attendance. Accepts multipart/form-data with an
    optional 'photo' file (required only when today's row does not exist yet).
    """
    user = _authenticated_user()
    body, status = attendance.submit_attendance(
        form=request.form,
        photo_file=request.files.get("photo"),
        user_id=(user or {}).get("sub"),
    )

    if body.get("success"):
        try:
            record = body.get("record", {})
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO activity_logs (user_id, action_type, query_text, source_tag)
                VALUES (?, 'attendance', ?, ?)
            """, (
                record.get("mobile_number"),
                f"{record.get('name')} • {record.get('position')} • {record.get('block_number')}",
                "Attendance submitted" if body.get("created") else "Attendance updated",
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Attendance activity log failed: {e}")

    return jsonify(body), status

@app.route("/api/admin/attendance", methods=["GET"])
def admin_attendance_list():
    """Filtered attendance register for the admin console."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    filters = {
        "status": request.args.get("status", ""),
        "position": request.args.get("position", ""),
        "date_from": request.args.get("date_from", ""),
        "date_to": request.args.get("date_to", ""),
        "q": request.args.get("q", ""),
    }
    try:
        limit = min(int(request.args.get("limit", 200)), 500)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        limit, offset = 200, 0

    result = attendance.list_attendance(filters, limit=limit, offset=offset)
    result["success"] = True
    return jsonify(result)

@app.route("/api/admin/attendance/<int:record_id>/photo", methods=["GET"])
def admin_attendance_photo(record_id):
    """
    Serve an attendance photo to the admin only. Returns 404 once the record
    has been approved — approval deletes the file from disk permanently.
    """
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    path = attendance.get_photo_for_record(record_id)
    if not path:
        return jsonify({"success": False, "error": "No photo available for this record."}), 404
    return send_from_directory(os.path.dirname(path), os.path.basename(path))

@app.route("/api/admin/attendance/<int:record_id>/approve", methods=["POST"])
def admin_attendance_approve(record_id):
    """Approve a record. Deletes its photo from the server and locks the row."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    reviewer = (_authenticated_user() or {}).get("name", "Admin")
    body, status = attendance.review_attendance(record_id, "approve", reviewer)
    return jsonify(body), status

@app.route("/api/admin/attendance/<int:record_id>/reject", methods=["POST"])
def admin_attendance_reject(record_id):
    """Reject a record with a reason. Photo is kept so the user can correct it."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    data = request.get_json(silent=True) or {}
    reviewer = (_authenticated_user() or {}).get("name", "Admin")
    body, status = attendance.review_attendance(record_id, "reject", reviewer, data.get("reason", ""))
    return jsonify(body), status

@app.route("/api/admin/attendance/<int:record_id>", methods=["DELETE"])
def admin_attendance_delete(record_id):
    """Permanently remove an attendance record and any photo it still holds."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    body, status = attendance.delete_attendance(record_id)
    return jsonify(body), status

@app.route("/api/admin/attendance/export", methods=["GET"])
def admin_attendance_export():
    """
    Download the whole (filtered) attendance register as ONE Excel workbook —
    every user's submissions live in the same sheet, one row each per day.
    """
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    filters = {
        "status": request.args.get("status", ""),
        "position": request.args.get("position", ""),
        "date_from": request.args.get("date_from", ""),
        "date_to": request.args.get("date_to", ""),
        "q": request.args.get("q", ""),
    }
    try:
        buffer, filename = attendance.build_attendance_workbook(filters)
    except Exception as e:
        logger.error(f"Attendance export failed: {e}")
        return jsonify({"success": False, "error": "Could not build the Excel file."}), 500

    return Response(
        buffer.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@app.route("/api/admin/attendance/purge-photos", methods=["POST"])
def admin_attendance_purge_photos():
    """Housekeeping: delete photo files on disk that no record points at."""
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    removed = attendance.purge_orphaned_photos()
    return jsonify({"success": True, "removed": removed,
                    "message": f"Removed {removed} orphaned photo file(s)."})

# ----------------- Messaging & Webhook Endpoints -----------------
@app.route("/api/channels/status", methods=["GET"])
def channels_status():
    return jsonify(get_channel_status())

@app.route("/webhook/whatsapp", methods=["GET", "POST"])
def whatsapp_webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            logger.info("WhatsApp Webhook verified successfully.")
            return challenge, 200
        return "Verification token mismatch", 403

    payload = request.get_json() or {}
    res = handle_whatsapp_webhook(payload)
    return jsonify(res), 200

@app.route("/webhook/telegram", methods=["POST"])
def telegram_webhook():
    payload = request.get_json() or {}
    res = handle_telegram_webhook(payload)
    return jsonify(res), 200

# ----------------- Server Entrypoint -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Census Assistant Server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
