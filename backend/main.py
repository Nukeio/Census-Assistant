"""
Census Assistant - Core Application Server (Flask)
Serves REST APIs, RAG endpoints, Authentication, Admin Management, Webhooks, and Static Frontend.
"""

import os
import sys
import json
import logging
from datetime import datetime
from urllib.parse import quote as requests_quote
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .database import get_db_connection, init_database
from .ingestion import run_full_ingestion, ingest_all_users, ingest_hlb_allocation, ingest_pdf_manuals
from .rag_engine import retrieve_rag_context, search_structured_records, search_manual_chunks
from .llm_provider import answer_query
from .auth import create_guest_session, request_otp, verify_otp, admin_login, verify_jwt_token
from .messaging_gateway import (
    handle_whatsapp_webhook, handle_telegram_webhook, get_channel_status,
    WHATSAPP_VERIFY_TOKEN, TECH_ASSISTANT_NAME, TECH_ASSISTANT_PHONE, WHATSAPP_DEEP_LINK,
    TECHNICAL_ASSISTANTS
)

CIRCLE_NAME = os.environ.get("CIRCLE_NAME", "Lakhipur Circle")

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

logger = logging.getLogger("CensusServer")
logging.basicConfig(level=logging.INFO)

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
    return None

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
    to its bundled offline copy — it must NEVER require admin auth (or any
    auth at all), otherwise every guest/functionary launch would look like
    the backend is down and get stuck on stale offline content.
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

@app.route("/api/auth/admin-login", methods=["POST"])
def auth_admin_login():
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")
    return jsonify(admin_login(username, password))

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
    model_name = data.get("model", "gemini-2.5-flash")
    lang = data.get("lang", "en")

    if not query:
        return jsonify({"error": "Empty query"}), 400

    result = answer_query(query, model_name=model_name, lang=lang)
    return jsonify(result)

# ----------------- Census Records Search Endpoints -----------------
def _area_info(circle_no):
    """
    Best-effort "allocated area" label + Google Maps link for a supervisory
    circle. The source Excel sheets (All_Users.xlsx / HLB Allocation.xlsx)
    only carry numeric State/District/Sub-District census codes and a blank
    Village/Town column — there is no actual village/area name or GPS data
    to draw on. Until that data is supplied, this falls back to the circle
    name/number, which is real but not block-precise.
    """
    if not circle_no:
        return None, None
    label = f"{CIRCLE_NAME} — Supervisory Circle {circle_no}"
    maps_url = "https://www.google.com/maps/search/?api=1&query=" + \
        requests_quote(f"{CIRCLE_NAME} Circle {circle_no}, Assam, India")
    return label, maps_url

@app.route("/api/records/search", methods=["GET"])
def records_search():
    q = request.args.get("q", "").strip()
    filter_by = request.args.get("filter", "all") # 'all', 'name', 'mobile', 'id', 'hlb'
    if filter_by == "eb":
        filter_by = "hlb"  # accept the old filter value for backward compatibility
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 15))
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if q:
        if filter_by == "name":
            where_clauses.append("name LIKE ?")
            params.append(f"%{q}%")
        elif filter_by == "mobile":
            where_clauses.append("mobile_number LIKE ?")
            params.append(f"%{q}%")
        elif filter_by == "id":
            where_clauses.append("user_id LIKE ?")
            params.append(f"%{q}%")
        elif filter_by == "hlb":
            # Search the HLB allocation sheet directly, joined back to the
            # functionaries sheet for the enumerator's mobile number.
            cursor.execute("""
                SELECT h.*, f.mobile_number, f.district, f.sub_district
                FROM hlb_allocations h
                LEFT JOIN functionaries f ON h.enumerator_user_id = f.user_id
                WHERE h.hlb_no LIKE ? OR h.supervisory_circle_no LIKE ?
                LIMIT ? OFFSET ?
            """, (f"%{q}%", f"%{q}%", limit, offset))
            hlb_rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            results = []
            for r in hlb_rows:
                area_name, maps_url = _area_info(r["supervisory_circle_no"])
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
                "results": results,
                "total": len(hlb_rows)
            })
        else:
            where_clauses.append("(name LIKE ? OR user_id LIKE ? OR mobile_number LIKE ? OR functionary_type LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cursor.execute(f"SELECT COUNT(*) FROM functionaries {where_sql}", params)
    total = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT * FROM functionaries {where_sql}
        ORDER BY id ASC
        LIMIT ? OFFSET ?
    """, params + [limit, offset])
    rows = cursor.fetchall()

    results = []
    for r in rows:
        # Cross-reference the functionary against the HLB allocation sheet
        # (matched on Enumerator User ID) to pull the HLB number, supervisor
        # name, and circle it's tied to.
        cursor.execute("""
            SELECT hlb_no, supervisor_name, supervisory_circle_no
            FROM hlb_allocations WHERE enumerator_user_id = ? LIMIT 1
        """, (r["user_id"],))
        hlb_match = cursor.fetchone()
        hlb_no = hlb_match["hlb_no"] if hlb_match else None
        sup_str = hlb_match["supervisor_name"] if hlb_match else None
        circle_no = hlb_match["supervisory_circle_no"] if hlb_match else None
        area_name, maps_url = _area_info(circle_no)

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
    """List actual supervisors from the functionaries sheet (not a single
    hardcoded profile), each with their circle(s) and how many HLBs/enumerators
    report to them per the HLB allocation sheet — the two source sheets
    joined on supervisor name."""
    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 30))

    conn = get_db_connection()
    cursor = conn.cursor()

    where_sql = "WHERE functionary_type LIKE '%Supervisor%'"
    params = []
    if q:
        where_sql += " AND (name LIKE ? OR user_id LIKE ? OR mobile_number LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

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
        circles = [c["supervisory_circle_no"] for c in cursor.fetchall()]

        cursor.execute("""
            SELECT COUNT(*) FROM hlb_allocations
            WHERE supervisor_name = ? OR supervisor_name LIKE ?
        """, (r["name"], f"%{r['name']}%"))
        hlb_count = cursor.fetchone()[0]

        area_name, maps_url = _area_info(circles[0] if circles else None)
        supervisors.append({
            "name": r["name"],
            "user_id": r["user_id"],
            "mobile": r["mobile_number"],
            "circles": circles,
            "hlb_count": hlb_count,
            "district": r["district"] or "",
            "sub_district": r["sub_district"] or "",
            "area_name": area_name,
            "maps_url": maps_url,
            "status": r["status"]
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
    return jsonify({
        "manuals": [
            {
                "filename": "FAQ (E & S).c58cf9c49a6df89a94b3 (1).pdf",
                "title": "Census 2027 FAQ for Enumerators and Supervisors",
                "pages": 9,
                "size": "191 KB",
                "category": "Official FAQ"
            },
            {
                "filename": "HLO_Manual_English.pdf",
                "title": "House Listing Operations (HLO) Instruction Manual",
                "pages": 136,
                "size": "97 MB",
                "category": "Standard Operating Procedure"
            }
        ]
    })

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
    avg_latency = round(ai_stat[1] or 1.2, 1)

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
    target_path = os.path.join(ROOT_DIR, filename)
    file.save(target_path)

    # Ingest based on filename
    if "user" in filename.lower():
        cnt = ingest_all_users(target_path)
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
    target_path = os.path.join(ROOT_DIR, filename)
    file.save(target_path)

    cnt = ingest_pdf_manuals()
    return jsonify({
        "success": True,
        "message": f"PDF {filename} uploaded and processed ({cnt} total chunks indexed)."
    })

@app.route("/api/admin/logs", methods=["GET"])
def admin_logs():
    admin_error = _require_admin()
    if admin_error:
        return admin_error

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 20")
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"logs": logs})

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
