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

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "census_assistant.db")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CensusDB")

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn

def _ensure_column(cursor, table: str, column: str, ddl: str) -> None:
    """
    Add a column to an existing table if it isn't there yet.

    SQLite has no ALTER TABLE ... ADD COLUMN IF NOT EXISTS, and databases that
    already exist in production (PythonAnywhere's census_assistant.db) were
    created before these columns existed. Checking PRAGMA table_info keeps
    startup idempotent instead of relying on a caught exception.
    """
    existing = {row["name"] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        logger.info(f"Schema migration: added {table}.{column}")


def init_database():
    """Initialize SQLite database tables and Full-Text Search virtual tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ------------------------------------------------------------------ #
        # Core tables                                                          #
        # ------------------------------------------------------------------ #
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(hlb_no, enumerator_user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hlb_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hlb_no TEXT NOT NULL,
                village_ward_name TEXT,
                landmark TEXT,
                boundary_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(hlb_no)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hlb_descriptions_hlb_no ON hlb_descriptions(hlb_no)
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
            CREATE TABLE IF NOT EXISTS app_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                mobile_number TEXT UNIQUE,
                email TEXT UNIQUE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                functionary_type TEXT DEFAULT 'User',
                reset_token TEXT,
                reset_token_expires REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_search_quota (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_identifier TEXT NOT NULL,
                search_date TEXT NOT NULL,
                search_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_identifier, search_date)
            )
        """)

        # Authentication audit trail. Every login attempt, password change and
        # admin-initiated reset lands here, so a locked-out user or a suspicious
        # burst of failures can be investigated after the fact.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account TEXT,
                event TEXT NOT NULL,
                outcome TEXT,
                detail TEXT,
                actor TEXT,
                ip_address TEXT,
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

        # Field attendance register (one row per mobile number per IST day).
        # Imported here rather than at module scope to avoid a circular import
        # — attendance.py imports get_db_connection from this module.
        from .attendance import init_attendance_schema
        init_attendance_schema(cursor)

        # ------------------------------------------------------------------ #
        # Performance indexes                                                  #
        # ------------------------------------------------------------------ #
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_functionaries_name ON functionaries(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_functionaries_mobile ON functionaries(mobile_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_users_mobile ON app_users(mobile_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_quota_user_date ON user_search_quota(user_identifier, search_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_audit_account ON auth_audit(account, created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_audit_created ON auth_audit(created_at)")

        # ------------------------------------------------------------------ #
        # Column migrations for databases created by an earlier version       #
        # ------------------------------------------------------------------ #
        # must_change_password backs the walk-in support flow: an admin sets a
        # temporary password, and the user is forced to choose a new one on
        # their next sign-in. failed_attempts/locked_until throttle password
        # guessing without ever needing the password itself in readable form.
        _ensure_column(cursor, "app_users", "must_change_password", "INTEGER DEFAULT 0")
        _ensure_column(cursor, "app_users", "failed_attempts", "INTEGER DEFAULT 0")
        _ensure_column(cursor, "app_users", "locked_until", "REAL")
        _ensure_column(cursor, "app_users", "last_login_at", "TIMESTAMP")
        _ensure_column(cursor, "app_users", "status", "TEXT DEFAULT 'ACTIVE'")
        _ensure_column(cursor, "admin_users", "must_change_password", "INTEGER DEFAULT 0")
        _ensure_column(cursor, "admin_users", "failed_attempts", "INTEGER DEFAULT 0")
        _ensure_column(cursor, "admin_users", "locked_until", "REAL")
        _ensure_column(cursor, "admin_users", "last_login_at", "TIMESTAMP")
        _ensure_column(cursor, "admin_users", "reset_token", "TEXT")
        _ensure_column(cursor, "admin_users", "reset_token_expires", "REAL")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hlb_allocations_hlb_no ON hlb_allocations(hlb_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hlb_allocations_circle ON hlb_allocations(supervisory_circle_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hlb_allocations_user ON hlb_allocations(enumerator_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_type ON activity_logs(action_type)")

        # ------------------------------------------------------------------ #
        # FTS5 Virtual Tables                                                  #
        # ------------------------------------------------------------------ #
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

            # manual_chunks_fts uses the Porter stemmer (unlike the two FTS
            # tables above, which index proper nouns/IDs where stemming
            # would hurt exact matches). Guideline/FAQ text needs it badly —
            # without it, a search for "definition" never matches text that
            # says "defined", "duties" never matches "duty", etc.
            #
            # SMART REBUILD: only DROP + CREATE + rebuild the FTS index if
            # the manual_chunks row count changed since last startup — for a
            # 97-MB PDF this rebuild otherwise blocks the WSGI worker for
            # several seconds on every cold start.
            current_chunk_count = cursor.execute("SELECT COUNT(*) FROM manual_chunks").fetchone()[0]
            stored_setting = cursor.execute(
                "SELECT value FROM system_settings WHERE key='manual_fts_last_chunk_count'"
            ).fetchone()
            last_known_count = int(stored_setting["value"]) if stored_setting else -1

            if current_chunk_count != last_known_count:
                logger.info(
                    f"manual_chunks changed ({last_known_count} → {current_chunk_count}): "
                    "rebuilding FTS index..."
                )
                cursor.execute("DROP TABLE IF EXISTS manual_chunks_fts")
                cursor.execute("""
                    CREATE VIRTUAL TABLE manual_chunks_fts USING fts5(
                        source_file, doc_title, page_number, section_header, chunk_text,
                        content='manual_chunks', content_rowid='id',
                        tokenize = 'porter unicode61'
                    )
                """)
                cursor.execute("INSERT INTO manual_chunks_fts(manual_chunks_fts) VALUES('rebuild')")
                cursor.execute("""
                    INSERT INTO system_settings(key, value) VALUES('manual_fts_last_chunk_count', ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
                """, (str(current_chunk_count),))
                logger.info("manual_chunks FTS rebuild complete.")
            else:
                # Ensure the FTS table exists even when chunk count hasn't changed
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS manual_chunks_fts USING fts5(
                        source_file, doc_title, page_number, section_header, chunk_text,
                        content='manual_chunks', content_rowid='id',
                        tokenize = 'porter unicode61'
                    )
                """)

        except sqlite3.OperationalError as e:
            logger.warning(f"FTS5 setup note: {e}")

        # ------------------------------------------------------------------ #
        # Admin account seed — PBKDF2-SHA256 (replaces plain SHA-256)         #
        # ------------------------------------------------------------------ #
        # Import here to avoid a circular import at module load time.
        from .auth import hash_password

        admin_username = os.environ.get("ADMIN_USERNAME", "shahinxsha")
        admin_password = os.environ.get("ADMIN_PASSWORD", "TechAss@99")
        admin_pass_hash = hash_password(admin_password)  # PBKDF2, random salt

        # Keep exactly one admin: the Technical Assistant account.
        cursor.execute("DELETE FROM admin_users WHERE username != ?", (admin_username,))
        cursor.execute("""
            INSERT INTO admin_users (username, password_hash, full_name, role)
            VALUES (?, ?, 'Shahin Sha A. (Technical Assistant)', 'admin')
            ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash
        """, (admin_username, admin_pass_hash))

        # ------------------------------------------------------------------ #
        # System settings defaults                                             #
        # ------------------------------------------------------------------ #
        default_settings = {
            "active_model": "gemini-3.6-flash",
            "available_models": json.dumps(["gemini-3.6-flash", "gemini-2.5-pro", "gpt-4o", "claude-3-5-sonnet"]),
            "technical_assistant_name": "Shahin Sha A.",
            "technical_assistant_phone": "+91 84534 41975",
            "technical_assistant_wa_link": "https://wa.me/918453441975",
            "technical_assistant_2_name": "S. A. Ahmed",
            "technical_assistant_2_phone": "+91 69019 80926",
            "technical_assistant_2_wa_link": "https://wa.me/916901980926",
            "circle_name": "Lakhipur Circle",
            "last_sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sync_status": "Synced"
        }
        for k, v in default_settings.items():
            cursor.execute("""
                INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)
            """, (k, v))

        # ------------------------------------------------------------------ #
        # Notifications are never auto-seeded with placeholder/mockup content.
        # The table starts empty and is only ever populated by real admin
        # broadcasts via POST /api/notifications (see main.py), so nothing
        # here can resurface stale demo alerts after a force sync or restart.
        # ------------------------------------------------------------------ #

        # ------------------------------------------------------------------ #
        # Seed initial activity logs (only if table is empty)                  #
        # ------------------------------------------------------------------ #
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
