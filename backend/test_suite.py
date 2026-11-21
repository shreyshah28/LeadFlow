import os
import sys
import io
from datetime import date, timedelta
import sqlite3

# Ensure backend dir is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Verify real DB count before running tests
LIVE_DB_FILE = os.path.join(backend_dir, "leadflow.db")
conn_live = sqlite3.connect(LIVE_DB_FILE)
c_live = conn_live.cursor()
c_live.execute("SELECT count(*) FROM leads")
live_initial_count = c_live.fetchone()[0]
conn_live.close()
print(f"[Safety Check] Real production DB verified at: {LIVE_DB_FILE} with {live_initial_count} records.")

# Use isolated test database
TEST_DB_FILE = os.path.join(backend_dir, "test_leadflow.db")
if os.path.exists(TEST_DB_FILE):
    try:
        os.remove(TEST_DB_FILE)
    except Exception:
        pass

# Configure test database engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

test_engine = create_engine(
    f"sqlite:///{TEST_DB_FILE}",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

import models
import database
import migrate_db
from main import app, get_db

# Override get_db dependency for tests to use isolated test DB
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
models.Base.metadata.create_all(bind=test_engine)

from fastapi.testclient import TestClient

passed_tests = []
failed_tests = []

def record_test(name, passed, detail=""):
    if passed:
        passed_tests.append(name)
        print(f"  [PASS] {name} {detail}")
    else:
        failed_tests.append(name)
        print(f"  [FAIL] {name} {detail}")

with TestClient(app) as client:
    print("=" * 60)
    print("RUNNING LEADFLOW COMPREHENSIVE QA & DATABASE TEST SUITE")
    print("=" * 60)

    # 1. Healthcheck
    print("\n1. Testing API Health Check...")
    res = client.get("/api/health")
    record_test("Healthcheck endpoint returns 200", res.status_code == 200 and res.json().get("status") == "ok")

    # 2. Schema Validation Tests
    print("\n2. Testing Schema & Model Validation...")
    # Empty company name
    res = client.post("/api/leads", json={"companyName": "", "followUpDate": "2026-11-25"})
    record_test("Reject empty company name (400 or 422)", res.status_code in [400, 422])

    # Whitespace-only company name
    res = client.post("/api/leads", json={"companyName": "   ", "followUpDate": "2026-11-25"})
    record_test("Reject whitespace-only company name (400 or 422)", res.status_code in [400, 422])

    # Missing follow-up date
    res = client.post("/api/leads", json={"companyName": "Acme Inc", "followUpDate": ""})
    record_test("Reject missing follow-up date (400 or 422)", res.status_code in [400, 422])

    # Invalid email format (when provided)
    res = client.post("/api/leads", json={"companyName": "Acme Inc", "email": "notanemail", "followUpDate": "2026-11-25"})
    record_test("Reject invalid email format (400 or 422)", res.status_code in [400, 422])

    # Negative deal value
    res = client.post("/api/leads", json={"companyName": "Acme Inc", "dealValue": -500, "followUpDate": "2026-11-25"})
    record_test("Reject negative deal value (400 or 422)", res.status_code in [400, 422])

    # Invalid status
    res = client.post("/api/leads", json={"companyName": "Acme Inc", "status": "InvalidStatus", "followUpDate": "2026-11-25"})
    record_test("Reject invalid status value (400 or 422)", res.status_code in [400, 422])

    # Support optional fields: minimal lead creation
    res = client.post("/api/leads", json={"companyName": "Minimal Corp", "followUpDate": "2026-11-25"})
    record_test("Allow optional contact/email/phone/city with defaults", res.status_code == 201)
    min_lead = res.json()
    record_test("Default city assigned 'Unknown'", min_lead.get("city") == "Unknown")
    record_test("Default status assigned 'New'", min_lead.get("status") == "New")
    record_test("Default dealValue assigned 0.0", min_lead.get("dealValue") == 0.0)

    # 3. Timestamp Integrity (created_at & updated_at)
    print("\n3. Testing Timestamp Integrity (created_at & updated_at)...")
    record_test("Lead response includes createdAt ISO string", bool(min_lead.get("createdAt")))
    record_test("Lead response includes updatedAt ISO string", bool(min_lead.get("updatedAt")))

    # 4. Create Full Valid Leads
    print("\n4. Testing Full CRUD Operations...")
    today_str = date.today().strftime("%Y-%m-%d")
    overdue_str = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
    upcoming_str = (date.today() + timedelta(days=4)).strftime("%Y-%m-%d")

    lead1_data = {
        "companyName": "Starlight Technologies",
        "contactPerson": "Sarah Connor",
        "email": "sarah@starlight.io",
        "phone": "+1 (555) 100-2000",
        "city": "San Francisco",
        "status": "New",
        "followUpDate": overdue_str,
        "dealValue": 32000,
        "notes": "Initial demo request"
    }
    res = client.post("/api/leads", json=lead1_data)
    record_test("Create valid lead 1 (Overdue)", res.status_code == 201)
    lead1 = res.json()
    lead1_id = lead1.get("id")

    lead2_data = {
        "companyName": "Vortex Energy Solutions",
        "contactPerson": "Tom Hanks",
        "email": "tom@vortexenergy.com",
        "phone": "+1 (555) 200-3000",
        "city": "Austin",
        "status": "Contacted",
        "followUpDate": today_str,
        "dealValue": 45000,
        "notes": "Follow-up call today"
    }
    res = client.post("/api/leads", json=lead2_data)
    record_test("Create valid lead 2 (Due Today)", res.status_code == 201)
    lead2 = res.json()
    lead2_id = lead2.get("id")

    lead3_data = {
        "companyName": "Zenith Cloud Corp",
        "contactPerson": "Maya Lin",
        "email": "maya@zenithcloud.org",
        "phone": "+1 (555) 300-4000",
        "city": "Seattle",
        "status": "Won",
        "followUpDate": upcoming_str,
        "dealValue": 60000,
        "notes": "Contract signed"
    }
    res = client.post("/api/leads", json=lead3_data)
    record_test("Create valid lead 3 (Won & Upcoming)", res.status_code == 201)
    lead3 = res.json()
    lead3_id = lead3.get("id")

    # Read single lead
    res = client.get(f"/api/leads/{lead1_id}")
    record_test("Read single lead by ID", res.status_code == 200 and res.json().get("companyName") == "Starlight Technologies")

    res = client.get("/api/leads/999999")
    record_test("Read non-existing lead returns 404", res.status_code == 404)

    # Update lead (PUT)
    res = client.put(f"/api/leads/{lead1_id}", json={"status": "Meeting", "dealValue": 38000})
    record_test("Update lead status & deal value", res.status_code == 200 and res.json().get("status") == "Meeting" and res.json().get("dealValue") == 38000)
    record_test("PUT updates updatedAt timestamp", bool(res.json().get("updatedAt")))

    # Reject negative deal value on update
    res = client.put(f"/api/leads/{lead1_id}", json={"dealValue": -100})
    record_test("Reject update with negative deal value (400 or 422)", res.status_code in [400, 422])

    res = client.put(f"/api/leads/{lead1_id}", json={"email": "bademail"})
    record_test("Reject update with invalid email (400 or 422)", res.status_code in [400, 422])

    res = client.put("/api/leads/999999", json={"status": "Meeting"})
    record_test("Update non-existing lead returns 404", res.status_code == 404)

    # 5. Dashboard Stats Computation
    print("\n5. Testing Dashboard Stats Computation...")
    res = client.get("/api/stats")
    stats = res.json()
    record_test("Dashboard stats: Total leads count == 4", stats.get("total_leads") == 4)
    record_test("Dashboard stats: Won leads count == 1", stats.get("won_leads") == 1)
    record_test("Dashboard stats: Meetings count == 1", stats.get("meetings") == 1)
    record_test("Dashboard stats: Contacted count == 1", stats.get("contacted") == 1)
    record_test("Dashboard stats: Overdue count == 1", stats.get("overdue_leads") == 1)
    record_test("Dashboard stats: Due Today count == 1", stats.get("due_today_leads") == 1)

    # 6. Search and Filtering
    print("\n6. Testing Search and Filtering...")
    res = client.get("/api/leads?search=starlight")
    record_test("Search by company name", len(res.json()) == 1 and res.json()[0]["companyName"] == "Starlight Technologies")

    res = client.get("/api/leads?search=Hanks")
    record_test("Search by contact person", len(res.json()) == 1 and res.json()[0]["contactPerson"] == "Tom Hanks")

    res = client.get("/api/leads?status=Meeting")
    record_test("Filter by status", len(res.json()) == 1 and res.json()[0]["status"] == "Meeting")

    # 7. Sorting
    print("\n7. Testing Sorting...")
    res = client.get("/api/leads?sortBy=dealValue&sortOrder=asc")
    asc_leads = res.json()
    record_test("Sort by dealValue ascending", asc_leads[0]["dealValue"] <= asc_leads[-1]["dealValue"])

    res = client.get("/api/leads?sortBy=dealValue&sortOrder=desc")
    desc_leads = res.json()
    record_test("Sort by dealValue descending", desc_leads[0]["dealValue"] >= desc_leads[-1]["dealValue"])

    # 8. Delete Lead
    print("\n8. Testing Lead Deletion...")
    res = client.delete(f"/api/leads/{min_lead['id']}")
    record_test("Delete lead returns 200", res.status_code == 200)

    # Verify deleted lead returns 404
    res = client.get(f"/api/leads/{min_lead['id']}")
    record_test("Verify deleted lead returns 404", res.status_code == 404)

    # 9. CSV Upload, Validation & Transaction Safety
    print("\n9. Testing CSV Upload & Transaction Safety...")
    valid_csv = """Company Name,Contact Person,Email,Phone,City,Status,Follow-up Date,Deal Value ($),Notes
Alpha Robotics,Alan Turing,alan@alpharobotics.com,+1 (555) 444-5555,Boston,New,2026-11-28,$28,000,Web lead
Beta Aerospace,Katherine Johnson,kj@betaaerospace.com,+1 (555) 555-6666,Huntsville,Contacted,2026-11-29,$55,000,Referral
Invalid Row Without Company,,valid@email.com,+1 555-7777,Dallas,New,2026-11-30,10000,Should skip
Invalid Row Bad Email,Bob Bad,bad_email_at_nowhere,+1 555-8888,Denver,New,2026-11-30,0,Should skip
"""
    files = {"file": ("leads.csv", valid_csv.encode("utf-8"), "text/csv")}
    res = client.post("/api/leads/upload-csv", files=files)
    record_test("Upload CSV with valid and invalid rows returns 200", res.status_code == 200)
    csv_res = res.json()
    record_test("CSV import: 2 valid rows imported", csv_res.get("imported_count") == 2)
    record_test("CSV import: 2 invalid rows skipped without crash", csv_res.get("skipped_count") == 2)
    record_test("CSV import: Error messages returned for skipped rows", len(csv_res.get("errors")) == 2)

    # Reject non-csv file
    files_txt = {"file": ("document.txt", b"plain text content", "text/plain")}
    res = client.post("/api/leads/upload-csv", files=files_txt)
    record_test("Reject non-CSV file upload (400)", res.status_code == 400)

    # Reject empty CSV
    files_empty = {"file": ("empty.csv", b"", "text/csv")}
    res = client.post("/api/leads/upload-csv", files=files_empty)
    record_test("Reject empty CSV file upload (400)", res.status_code == 400)

    # 10. City Name Normalization Tests
    print("\n10. Testing City Normalization...")
    lead_norm_data = {
        "companyName": "Norm City Corp",
        "contactPerson": "Norm Smith",
        "email": "norm@citycorp.com",
        "phone": "+1 555-0199",
        "city": "surat",
        "status": "New",
        "followUpDate": "2026-12-01",
        "dealValue": 5000
    }
    res = client.post("/api/leads", json=lead_norm_data)
    record_test("Create lead with lowercase city returns 201", res.status_code == 201)
    norm_lead = res.json()
    record_test("Lowercase city 'surat' normalized to 'Surat'", norm_lead.get("city") == "Surat")

    # Update with lowercase city
    res = client.put(f"/api/leads/{norm_lead['id']}", json={"city": "ahmedabad"})
    record_test("Update lead with lowercase city returns 200", res.status_code == 200)
    record_test("Updated city 'ahmedabad' normalized to 'Ahmedabad'", res.json().get("city") == "Ahmedabad")

    # CSV import with lowercase city
    norm_csv = """Company Name,Contact Person,Email,Phone,City,Status,Follow-up Date,Deal Value ($),Notes
City Test Co,Jane Norm,jane@citytest.com,+1 555-0200,san francisco,New,2026-12-05,$10000,Web lead
"""
    files_norm = {"file": ("city_norm.csv", norm_csv.encode("utf-8"), "text/csv")}
    res = client.post("/api/leads/upload-csv", files=files_norm)
    record_test("CSV import with lowercase city 'san francisco' returns 200", res.status_code == 200)
    res_leads = client.get("/api/leads?search=City%20Test%20Co")
    if res_leads.status_code == 200 and len(res_leads.json()) > 0:
        record_test("CSV city normalized to 'San Francisco'", res_leads.json()[0].get("city") == "San Francisco")
    else:
        record_test("CSV city normalized to 'San Francisco'", False)

    # 11. Database Migration Idempotence Test
    print("\n11. Testing Database Migration Idempotence...")
    mig_success = migrate_db.run_migration(TEST_DB_FILE)
    record_test("Migration executes safely and idempotently", mig_success)

    # 12. Sample Data Reset on Test DB
    print("\n12. Testing Sample Data Reset on Test Database...")
    fresh_session = TestingSessionLocal()
    fresh_session.query(models.Lead).delete()
    fresh_session.commit()
    fresh_session.close()

    res = client.post("/api/leads/reset-sample")
    record_test("Reset sample leads endpoint (200)", res.status_code == 200)
    fresh_session = TestingSessionLocal()
    sample_count = fresh_session.query(models.Lead).count()
    fresh_session.close()
    record_test("Reset restored exactly 12 sample leads on test DB", sample_count == 12)

# Teardown test database file
try:
    test_engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    print("\nTemporary test database cleaned up.")
except Exception as e:
    print(f"Notice: test db cleanup: {e}")

# Verify production database count has not been touched
conn_live = sqlite3.connect(LIVE_DB_FILE)
c_live = conn_live.cursor()
c_live.execute("SELECT count(*) FROM leads")
live_final_count = c_live.fetchone()[0]
conn_live.close()

print("\n" + "=" * 60)
print(f"[DATA PRESERVATION CHECK] Real DB count before: {live_initial_count}, after: {live_final_count}")
print(f"TEST RESULTS: {len(passed_tests)} Passed, {len(failed_tests)} Failed")
print("=" * 60)

assert live_final_count == live_initial_count, f"CRITICAL: Real DB changed from {live_initial_count} to {live_final_count}!"

if failed_tests:
    print("FAILED TESTS:")
    for f in failed_tests:
        print(" -", f)
    sys.exit(1)
else:
    print("ALL TESTS PASSED WITH 100% SUCCESS RATE!")
    sys.exit(0)
