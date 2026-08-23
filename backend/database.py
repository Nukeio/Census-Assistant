"""
Census Assistant - Database Layer
Supports SQLite with FTS5 for local runtime and schema generation for Supabase / PostgreSQL.
"""

import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
# DATA_DIR points at a persistent volume in production (e.g. a mounted cloud
# disk) so the database survives redeploys/restarts. Defaults to ROOT_DIR for
# local/dev runs where no separate data volume is configured.
DATA_DIR = os.environ.get("DATA_DIR", ROOT_DIR)
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "census_assistant.db")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CensusDB")

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn

def init_database():
    """Initialize SQLite database tables and Full-Text Search virtual tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Tables creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS functionaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sno INTEGER,
                user_id TEXT UNIQUE NOT NULL,
                functionary_type TEXT,
                name TEXT NOT NULL,
                mobile_number TEXT,
                state_ut TEXT,
                district TEXT,
                sub_district TEXT,
                village_town TEXT,
                status TEXT DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hlb_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supervisory_circle_no TEXT,
                hlb_no TEXT NOT NULL,
                supervisor_name TEXT,
                enumerator_name TEXT,
                enumerator_user_id TEXT,
                allotment_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manual_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                doc_title TEXT NOT NULL,
                page_number INTEGER,
                section_header TEXT,
                chunk_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'Notices',
                priority TEXT DEFAULT 'normal',
                badge TEXT,
                timestamp_str TEXT,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action_type TEXT,
                query_text TEXT,
                source_tag TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                query_count INTEGER DEFAULT 1,
                latency_ms REAL,
                status TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # FTS5 Virtual Tables
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS functionaries_fts USING fts5(
                    user_id, functionary_type, name, mobile_number, district, sub_district, village_town,
                    content='functionaries', content_rowid='id'
                )
            """)
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS hlb_allocations_fts USING fts5(
                    supervisory_circle_no, hlb_no, supervisor_name, enumerator_name, enumerator_user_id,
                    content='hlb_allocations', content_rowid='id'
                )
            """)
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS manual_chunks_fts USING fts5(
                    source_file, doc_title, page_number, section_header, chunk_text,
                    content='manual_chunks', content_rowid='id'
                )
            """)
        except sqlite3.OperationalError as e:
            logger.warning(f"FTS5 setup note: {e}")

        # Seed Default Admin (admin / admin123)
        import hashlib
        admin_pass_hash = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
        cursor.execute("""
            INSERT OR IGNORE INTO admin_users (username, password_hash, full_name, role)
            VALUES ('admin', ?, 'Census Admin Officer', 'admin')
        """, (admin_pass_hash,))

        # Seed Default System Settings
        default_settings = {
            "active_model": "gemini-2.5-flash",
            "available_models": json.dumps(["gemini-2.5-flash", "gemini-2.5-pro", "gpt-4o", "claude-3-5-sonnet"]),
            "technical_assistant_name": "Shahin Sha A.",
            "technical_assistant_phone": "+91 84534 41975",
            "technical_assistant_wa_link": "https://wa.me/918453441975",
            "supervisor_name": "S. A. Ahmed",
            "circle_name": "Lakhipur Circle",
            "last_sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sync_status": "Synced"
        }

        for k, v in default_settings.items():
            cursor.execute("""
                INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)
            """, (k, v))

        # Seed Initial Notifications
        cursor.execute("SELECT COUNT(*) FROM notifications")
        if cursor.fetchone()[0] == 0:
            sample_notifs = [
                ("Meeting Schedule - Oct 25", "Mandatory briefing for regional coordinators regarding data collection protocols and verification workflows.", "Notices", "normal", "Oct 25", "2 hours ago"),
                ("New Demographic Database Uploaded", "The latest demographic dataset for Lakhipur Circle has been successfully integrated into the central knowledge repository.", "Alerts", "normal", "Database", "Yesterday"),
                ("Census Deadline Extension", "Due to field operations requirements in northern districts, the house listing submission deadline has been extended by 48 hours.", "Alerts", "urgent", "Urgent", "Oct 20")
            ]
            for title, content, cat, prio, badge, ts in sample_notifs:
                cursor.execute("""
                    INSERT INTO notifications (title, content, category, priority, badge, timestamp_str)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, content, cat, prio, badge, ts))

        # Seed Initial Recent Activity
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        if cursor.fetchone()[0] == 0:
            sample_activities = [
                ("guest", "ai_query", "Household definition criteria", "Asked AI Assistant • 2 hours ago"),
                ("guest", "manual_search", "Form 4B Guidelines", "Manual Search • Yesterday"),
                ("guest", "task", "Weekly Report Submission", "Task Completed • Oct 24")
            ]
            for uid, act, query, tag in sample_activities:
                cursor.execute("""
                    INSERT INTO activity_logs (user_id, action_type, query_text, source_tag)
                    VALUES (?, ?, ?, ?)
                """, (uid, act, query, tag))

        conn.commit()
        logger.info("Database initialized successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
