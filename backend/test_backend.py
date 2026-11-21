import os
import sys

# Ensure backend dir is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

TEST_DB_FILE = os.path.join(backend_dir, "test_backend_isolated.db")
if os.path.exists(TEST_DB_FILE):
    try:
        os.remove(TEST_DB_FILE)
    except Exception:
        pass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

test_engine = create_engine(
    f"sqlite:///{TEST_DB_FILE}",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

import models
import database
from main import app, get_db, seed_sample_leads

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
models.Base.metadata.create_all(bind=test_engine)

# Seed sample leads into the isolated test db
with TestingSessionLocal() as session:
    seed_sample_leads(session)

from fastapi.testclient import TestClient

try:
    with TestClient(app) as client:
        print("1. Testing Health Endpoint:")
        res = client.get("/api/health")
        print("  status:", res.status_code, "body:", res.json())
        assert res.status_code == 200

        print("\n2. Testing Stats Endpoint:")
        res = client.get("/api/stats")
        print("  status:", res.status_code)
        assert res.status_code == 200
        stats = res.json()
        print("  Total leads:", stats.get("total_leads"), "pipelineValue:", stats.get("pipelineValue"), "overdue:", stats.get("overdue_leads"))
        assert stats.get("total_leads") >= 12

        print("\n3. Testing GET /api/leads:")
        res = client.get("/api/leads")
        print("  status:", res.status_code, "count:", len(res.json()))
        assert res.status_code == 200
        assert len(res.json()) >= 12
        sample_lead = res.json()[0]
        print("  First lead companyName:", sample_lead.get("companyName"), "followUpDate:", sample_lead.get("followUpDate"))

        print("\n4. Testing POST /api/leads:")
        new_lead_data = {
            "companyName": "Acme Test Robotics",
            "contactPerson": "Alice Wonder",
            "email": "alice@acmerobotics.com",
            "phone": "+1 (555) 999-8888",
            "city": "San Jose",
            "status": "New",
            "followUpDate": "2026-11-25",
            "dealValue": 35000,
            "notes": "Automated warehouse bot inquiry"
        }
        res = client.post("/api/leads", json=new_lead_data)
        print("  POST status:", res.status_code, "created id:", res.json().get("id"))
        assert res.status_code == 201
        created_id = res.json().get("id")

        print("\n5. Testing GET /api/leads/{id}:")
        res = client.get(f"/api/leads/{created_id}")
        print("  GET lead status:", res.status_code, "lead company:", res.json().get("companyName"))
        assert res.status_code == 200
        assert res.json().get("companyName") == "Acme Test Robotics"

        print("\n6. Testing PUT /api/leads/{id}:")
        res = client.put(f"/api/leads/{created_id}", json={"status": "Meeting", "dealValue": 40000})
        print("  PUT status:", res.status_code, "updated status:", res.json().get("status"), "updated value:", res.json().get("dealValue"))
        assert res.status_code == 200
        assert res.json().get("status") == "Meeting"
        assert res.json().get("dealValue") == 40000

        print("\n7. Testing DELETE /api/leads/{id}:")
        res = client.delete(f"/api/leads/{created_id}")
        print("  DELETE status:", res.status_code, "response:", res.json())
        assert res.status_code == 200

        # Verify 404
        res = client.get(f"/api/leads/{created_id}")
        print("  Verify 404 status:", res.status_code)
        assert res.status_code == 404

        print("\n8. Testing CSV Import:")
        csv_content = """Company Name,Contact Person,Email,Phone,City,Status,Follow-up Date,Deal Value ($),Notes
Test Company Alpha,John Smith,john@testalpha.com,+1 555-1111,Boston,New,2026-11-28,$15000,Web lead
Test Company Beta,Jane Doe,jane@testbeta.com,+1 555-2222,Austin,Contacted,2026-11-29,$22000,Referral
Invalid Row Without Email,Bob NoEmail,,+1 555-3333,Denver,New,2026-11-30,0,Should skip
"""
        files = {"file": ("test_import.csv", csv_content.encode("utf-8"), "text/csv")}
        res = client.post("/api/leads/upload-csv", files=files)
        print("  CSV Upload status:", res.status_code, "result:", res.json())
        assert res.status_code == 200
        import_result = res.json()
        assert import_result.get("imported_count") == 2
        assert import_result.get("skipped_count") == 1

        print("\nALL BACKEND TESTS PASSED SUCCESSFULLY!")

finally:
    app.dependency_overrides.clear()
    test_engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass
