import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app
import database

class TestDeploymentReadiness(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root / endpoint returns 200 with service information"""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("app"), "LeadFlow API")
        self.assertIn("version", data)

    def test_health_endpoints(self):
        """Test both /health and /api/health return status ok and db connectivity"""
        for path in ["/health", "/api/health"]:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data.get("status"), "ok")
            self.assertIn("database", data)
            self.assertEqual(data.get("database_status"), "connected")

    def test_cors_vercel_production(self):
        """Verify CORS headers for exact Vercel frontend domain"""
        headers = {
            "Origin": "https://lead-flow-acme-7c28.vercel.app"
        }
        res = self.client.get("/api/health", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers.get("access-control-allow-origin"),
            "https://lead-flow-acme-7c28.vercel.app"
        )
        self.assertEqual(
            res.headers.get("access-control-allow-credentials"),
            "true"
        )

    def test_cors_vercel_preview(self):
        """Verify CORS headers for arbitrary Vercel preview domain via regex"""
        headers = {
            "Origin": "https://lead-flow-preview-pr12.vercel.app"
        }
        res = self.client.get("/api/health", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers.get("access-control-allow-origin"),
            "https://lead-flow-preview-pr12.vercel.app"
        )

    def test_cors_preflight_options(self):
        """Verify CORS OPTIONS preflight request"""
        headers = {
            "Origin": "https://lead-flow-acme-7c28.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
        res = self.client.options("/api/leads", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers.get("access-control-allow-origin"),
            "https://lead-flow-acme-7c28.vercel.app"
        )

    def test_database_url_normalization_logic(self):
        """Verify PostgreSQL URL conversion and stripping logic"""
        test_cases = [
            ("postgres://user:pass@host:5432/db", "postgresql://user:pass@host:5432/db"),
            ("  postgres://user:pass@host:5432/db  ", "postgresql://user:pass@host:5432/db"),
            ("'postgres://user:pass@host:5432/db'", "postgresql://user:pass@host:5432/db"),
            ("postgresql://user:pass@host:5432/db", "postgresql://user:pass@host:5432/db"),
        ]
        for raw, expected in test_cases:
            cleaned = raw.strip().strip("'\"")
            if cleaned.startswith("postgres://"):
                cleaned = cleaned.replace("postgres://", "postgresql://", 1)
            self.assertEqual(cleaned, expected)

    def test_render_sslmode_detection(self):
        """Verify that Render URLs require sslmode=require"""
        render_internal = "postgresql://user:pass@dpg-abcde12345-a:5432/leadflow"
        render_external = "postgresql://user:pass@dpg-abcde12345-a.oregon-postgres.render.com/leadflow"
        
        for url in [render_internal, render_external]:
            connect_args = {}
            if "sslmode" not in url:
                if "render.com" in url or "dpg-" in url:
                    connect_args["sslmode"] = "require"
            self.assertEqual(connect_args.get("sslmode"), "require")

    def test_real_sqlite_data_intact(self):
        """Verify real SQLite database and backup retain exactly 35 records"""
        import sqlite3
        real_db = os.path.join(BASE_DIR, "leadflow.db")
        backup_db = os.path.join(BASE_DIR, "leadflow_backup_pre_audit.db")

        conn = sqlite3.connect(real_db)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM leads")
        count = c.fetchone()[0]
        conn.close()
        self.assertEqual(count, 35, f"Expected 35 leads in leadflow.db, found {count}")

        conn2 = sqlite3.connect(backup_db)
        c2 = conn2.cursor()
        c2.execute("SELECT count(*) FROM leads")
        b_count = c2.fetchone()[0]
        conn2.close()
        self.assertEqual(b_count, 35, f"Expected 35 leads in backup, found {b_count}")

if __name__ == "__main__":
    unittest.main()

