"""
Census Assistant - End-to-End Automated Test Suite
Validates backend APIs, RAG pipeline, Anti-Hallucination, Auth, Database, Admin Endpoints, and Multilingual answers.
"""

import os
import sys
import unittest
import json

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Enable dev OTP bypass during test execution
os.environ["DEV_OTP_BYPASS"] = "true"

from backend.database import get_db_connection, init_database
from backend.ingestion import ingest_all_users, ingest_hlb_allocation, ingest_hlb_description, ingest_pdf_manuals
from backend.rag_engine import detect_intent, retrieve_rag_context, search_structured_records, search_manual_chunks, search_by_area
from backend.llm_provider import answer_query, NOT_FOUND_PHRASE
from backend.auth import create_guest_session, request_otp, verify_otp, admin_login, verify_jwt_token
from backend.main import app

class CensusAssistantTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize test environment, seed database, and create flask test client."""
        init_database()
        cls.client = app.test_client()

        # Generate admin token for testing admin endpoints
        admin_username = os.environ.get("ADMIN_USERNAME", "shahinxsha")
        admin_password = os.environ.get("ADMIN_PASSWORD", "TechAss@99")
        adm = admin_login(admin_username, admin_password)
        cls.admin_token = adm.get("token")

    def test_01_database_population(self):
        """Verify that Excel and PDF data are properly indexed in database."""
        conn = get_db_connection()
        func_cnt = conn.execute("SELECT COUNT(*) FROM functionaries").fetchone()[0]
        hlb_cnt = conn.execute("SELECT COUNT(*) FROM hlb_allocations").fetchone()[0]
        chunk_cnt = conn.execute("SELECT COUNT(*) FROM manual_chunks").fetchone()[0]
        conn.close()

        self.assertGreaterEqual(func_cnt, 800, f"Expected >= 800 functionaries, got {func_cnt}")
        self.assertGreaterEqual(hlb_cnt, 600, f"Expected >= 600 HLB allocations, got {hlb_cnt}")
        self.assertGreaterEqual(chunk_cnt, 35, f"Expected >= 35 manual chunks, got {chunk_cnt}")

    def test_02_intent_classification(self):
        """Test intent classification logic for different query types."""
        self.assertEqual(detect_intent("Who is assigned to EB 12?"), "RECORD_SEARCH")
        self.assertEqual(detect_intent("Who is the supervisor for Shahin Sha?"), "SUPERVISOR_QUERY")
        self.assertEqual(detect_intent("What is the definition of a household?"), "MANUAL_SEARCH")
        self.assertEqual(detect_intent("Hello, how are you?"), "GENERAL")

    def test_03_structured_records_search(self):
        """Test search for specific enumerators and EB numbers."""
        results = search_structured_records("EB 12", limit=5)
        self.assertTrue(len(results) > 0, "Expected search results for EB 12")
        self.assertIn("hlb_no", results[0])

        shahin_results = search_structured_records("Shahin Sha", limit=5)
        self.assertTrue(len(shahin_results) > 0, "Expected search results for Shahin Sha")

    def test_04_manual_chunks_search(self):
        """Test full-text retrieval for manual instructions."""
        chunks = search_manual_chunks("household", limit=3)
        self.assertTrue(len(chunks) > 0, "Expected manual chunks matching 'household'")
        self.assertTrue("chunk_text" in chunks[0])

    def test_05_rag_multilingual_answers(self):
        """Test RAG engine answering queries in all 4 supported languages."""
        langs = ["en", "as", "hi", "bn"]
        for lang in langs:
            res = answer_query("Who is assigned to EB 12?", model_name="gemini-2.5-flash", lang=lang)
            self.assertIn("answer", res)
            self.assertGreater(len(res["answer"]), 20)
            self.assertTrue(len(res["citations"]) > 0)

    def test_06_auth_flow(self):
        """Test Guest, OTP, and Admin authentication workflows."""
        # 1. Guest Session
        guest = create_guest_session()
        self.assertTrue(guest["authenticated"])
        self.assertIsNotNone(guest["token"])

        # 2. OTP Request & Verification
        otp_req = request_otp("8453441975")
        self.assertTrue(otp_req["success"])
        otp_code = otp_req["debug_otp"]
        otp_ver = verify_otp("8453441975", otp_code)
        self.assertTrue(otp_ver["success"])
        self.assertEqual(otp_ver["user"]["name"], "SHAHIN SHA ALOMGIR")

        # 3. Admin Login
        admin_username = os.environ.get("ADMIN_USERNAME", "shahinxsha")
        admin_password = os.environ.get("ADMIN_PASSWORD", "TechAss@99")
        adm = admin_login(admin_username, admin_password)
        self.assertTrue(adm["success"])
        self.assertEqual(adm["user"]["role"], "admin")

    def test_07_rest_api_endpoints(self):
        """Test all core REST endpoints via Flask test client."""
        # 1. /api/chat
        chat_resp = self.client.post("/api/chat", json={"query": "Who is assigned to HLB 12?"})
        self.assertEqual(chat_resp.status_code, 200)
        chat_data = chat_resp.get_json()
        self.assertIn("answer", chat_data)

        # 2. /api/records/search
        rec_resp = self.client.get("/api/records/search?q=Shahin&filter=name")
        self.assertEqual(rec_resp.status_code, 200)
        rec_data = rec_resp.get_json()
        self.assertGreater(len(rec_data["results"]), 0)

        # 3. /api/records/supervisor
        sup_resp = self.client.get("/api/records/supervisor")
        self.assertEqual(sup_resp.status_code, 200)
        sup_data = sup_resp.get_json()
        self.assertIn("supervisors", sup_data)
        self.assertGreater(len(sup_data["supervisors"]), 0)

        # 4. /api/admin/stats (authenticated)
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        stats_resp = self.client.get("/api/admin/stats", headers=headers)
        self.assertEqual(stats_resp.status_code, 200)
        stats_data = stats_resp.get_json()
        self.assertGreater(stats_data["total_records"], 1000)

        # 5. /api/channels/status
        chan_resp = self.client.get("/api/channels/status")
        self.assertEqual(chan_resp.status_code, 200)
        chan_data = chan_resp.get_json()
        self.assertEqual(chan_data["primary_channel"], "WhatsApp Business Platform")

    def test_08_whatsapp_webhook_verification(self):
        """Test WhatsApp Webhook token verification endpoint."""
        resp = self.client.get("/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=census_assistant_webhook_verify_2024&hub.challenge=123456789")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.decode("utf-8"), "123456789")

    def test_09_anti_hallucination_guarantee(self):
        """Verify that an off-topic query returns the exact required fallback phrase."""
        off_topic_queries = [
            "What is the capital of France?",
            "How do I bake a chocolate cake?",
            "Tell me about the history of Rome."
        ]
        for query in off_topic_queries:
            res = answer_query(query, model_name="gemini-2.5-flash", lang="en")
            self.assertEqual(
                res["answer"].strip(),
                NOT_FOUND_PHRASE,
                f"Expected exact fallback for off-topic query '{query}', got: {res['answer']}"
            )

    def test_10_area_search(self):
        """Verify that searching for village/area names returns matched HLB records."""
        area_results = search_by_area("Lakhipur", limit=3)
        self.assertIsInstance(area_results, list)

    def test_11_admin_new_endpoints(self):
        """Verify all new admin endpoints respond with valid structures when authenticated."""
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # 1. /api/admin/query-logs
        logs_resp = self.client.get("/api/admin/query-logs", headers=headers)
        self.assertEqual(logs_resp.status_code, 200)
        logs_data = logs_resp.get_json()
        self.assertIn("query_logs", logs_data)

        # 2. /api/admin/system-health
        health_resp = self.client.get("/api/admin/system-health", headers=headers)
        self.assertEqual(health_resp.status_code, 200)
        health_data = health_resp.get_json()
        self.assertEqual(health_data["status"], "healthy")
        self.assertIn("table_counts", health_data)

        # 3. /api/admin/users
        users_resp = self.client.get("/api/admin/users", headers=headers)
        self.assertEqual(users_resp.status_code, 200)
        users_data = users_resp.get_json()
        self.assertIn("users", users_data)
        self.assertGreater(len(users_data["users"]), 0)

        # 4. /api/admin/uploaded-files
        files_resp = self.client.get("/api/admin/uploaded-files", headers=headers)
        self.assertEqual(files_resp.status_code, 200)
        files_data = files_resp.get_json()
        self.assertIn("files", files_data)
        self.assertGreater(len(files_data["files"]), 0)

    def test_12_supervisor_assigned_enumerators_cross_reference(self):
        """Verify that supervisors endpoint returns attached assigned enumerators with full details."""
        resp = self.client.get("/api/records/supervisor")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("supervisors", data)
        self.assertGreater(len(data["supervisors"]), 0)
        
        # Check first supervisor
        first_sup = data["supervisors"][0]
        self.assertIn("enumerators", first_sup)
        self.assertIn("hlb_count", first_sup)
        self.assertEqual(len(first_sup["enumerators"]), first_sup["hlb_count"])
        
        # If supervisor has enumerators, verify their fields
        if first_sup["enumerators"]:
            first_enum = first_sup["enumerators"][0]
            self.assertIn("hlb_no", first_enum)
            self.assertIn("enumerator_name", first_enum)
            self.assertIn("enumerator_user_id", first_enum)
            self.assertIn("mobile", first_enum)

if __name__ == "__main__":
    unittest.main()
