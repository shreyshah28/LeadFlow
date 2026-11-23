import os
import sys

# Ensure backend directory is in sys.path regardless of working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import io
import csv
from datetime import datetime, date, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, text

import models
import schemas
import database
from database import engine, get_db, SessionLocal, Base, is_sqlite
import migrate_db
import email_service

def get_relative_date(offset_days: int) -> str:
    target = date.today() + timedelta(days=offset_days)
    return target.strftime("%Y-%m-%d")

def normalize_city_name(city: Optional[str]) -> str:
    if not city:
        return "Unknown"
    cleaned = city.strip()
    if not cleaned:
        return "Unknown"
    return " ".join(word.capitalize() for word in cleaned.split())

def seed_sample_leads(db_session: Optional[Session] = None):
    should_close = False
    if db_session is None:
        db = SessionLocal()
        should_close = True
    else:
        db = db_session

    try:
        count = db.query(models.Lead).count()
        if count == 0:
            sample_leads = [
                {
                    "company_name": "Apex Logistics Corp",
                    "contact_person": "David Miller",
                    "email": "david.miller@apexlogistics.com",
                    "phone": "+1 (555) 234-8901",
                    "city": "Chicago",
                    "status": "Contacted",
                    "follow_up_date": get_relative_date(-2),  # Overdue by 2 days
                    "deal_value": 24500.0,
                    "notes": "Interested in enterprise fleet routing add-on. Sent pricing deck."
                },
                {
                    "company_name": "NovaTech Solutions",
                    "contact_person": "Sarah Jenkins",
                    "email": "sjenkins@novatech.io",
                    "phone": "+1 (555) 345-6789",
                    "city": "San Francisco",
                    "status": "Meeting",
                    "follow_up_date": get_relative_date(0),   # Due Today
                    "deal_value": 48000.0,
                    "notes": "Technical architecture review call scheduled for 2:30 PM."
                },
                {
                    "company_name": "Horizon Retail Partners",
                    "contact_person": "Marcus Vance",
                    "email": "marcus@horizonretail.com",
                    "phone": "+1 (555) 456-7890",
                    "city": "New York",
                    "status": "New",
                    "follow_up_date": get_relative_date(-3),  # Overdue by 3 days
                    "deal_value": 18000.0,
                    "notes": "Inbound lead from product webinar. Needs discovery call."
                },
                {
                    "company_name": "BluePeak Analytics",
                    "contact_person": "Elena Rostova",
                    "email": "elena.r@bluepeakanalytics.com",
                    "phone": "+1 (555) 567-8901",
                    "city": "Seattle",
                    "status": "Won",
                    "follow_up_date": get_relative_date(-5),
                    "deal_value": 65000.0,
                    "notes": "Signed 1-year annual contract. Handed over to Customer Success."
                },
                {
                    "company_name": "CloudScale AI Labs",
                    "contact_person": "Julian Chen",
                    "email": "jchen@cloudscale.ai",
                    "phone": "+1 (555) 678-9012",
                    "city": "Austin",
                    "status": "Meeting",
                    "follow_up_date": get_relative_date(0),   # Due Today
                    "deal_value": 52000.0,
                    "notes": "Budget approved by VP of Engineering. Contract negotiation stage."
                },
                {
                    "company_name": "GreenPulse Energy",
                    "contact_person": "Rachel Adams",
                    "email": "rachel@greenpulseenergy.com",
                    "phone": "+1 (555) 789-0123",
                    "city": "Denver",
                    "status": "Contacted",
                    "follow_up_date": get_relative_date(1),   # Tomorrow
                    "deal_value": 31000.0,
                    "notes": "Follow up on security compliance questionnaire response."
                },
                {
                    "company_name": "SwiftPay Networks",
                    "contact_person": "Karan Patel",
                    "email": "karan@swiftpay.org",
                    "phone": "+1 (555) 890-1234",
                    "city": "Atlanta",
                    "status": "Won",
                    "follow_up_date": get_relative_date(-8),
                    "deal_value": 84000.0,
                    "notes": "Payment gateway integration pilot succeeded. Enterprise license active."
                },
                {
                    "company_name": "Lumina Health Systems",
                    "contact_person": "Dr. Rebecca Thorne",
                    "email": "rthorne@luminahealth.org",
                    "phone": "+1 (555) 901-2345",
                    "city": "Boston",
                    "status": "New",
                    "follow_up_date": get_relative_date(2),   # In 2 days
                    "deal_value": 39500.0,
                    "notes": "HIPAA certification confirmed. Scheduled initial phone call."
                },
                {
                    "company_name": "MetroSupply Distribution",
                    "contact_person": "Carlos Delgado",
                    "email": "carlos@metrosupply.com",
                    "phone": "+1 (555) 012-3456",
                    "city": "Dallas",
                    "status": "Lost",
                    "follow_up_date": get_relative_date(-12),
                    "deal_value": 15000.0,
                    "notes": "Decided to renew with legacy vendor due to fiscal budget constraints."
                },
                {
                    "company_name": "Vanguard CyberSec",
                    "contact_person": "Priya Sharma",
                    "email": "psharma@vanguardcyber.net",
                    "phone": "+1 (555) 123-4567",
                    "city": "San Francisco",
                    "status": "Contacted",
                    "follow_up_date": get_relative_date(3),   # In 3 days
                    "deal_value": 42000.0,
                    "notes": "Expressed strong interest in API rate limiting and webhook security."
                },
                {
                    "company_name": "Beacon Commerce Group",
                    "contact_person": "Arthur Pendelton",
                    "email": "arthur@beaconcommerce.co",
                    "phone": "+1 (555) 234-5678",
                    "city": "Miami",
                    "status": "Meeting",
                    "follow_up_date": get_relative_date(5),   # In 5 days
                    "deal_value": 37000.0,
                    "notes": "Demonstrating automated lead scoring feature to regional team."
                },
                {
                    "company_name": "Nexus FinTech Labs",
                    "contact_person": "Sophia Williams",
                    "email": "sophia.williams@nexusfintech.io",
                    "phone": "+1 (555) 345-7890",
                    "city": "New York",
                    "status": "Won",
                    "follow_up_date": get_relative_date(-1),
                    "deal_value": 72000.0,
                    "notes": "Multi-year contract finalized. Onboarding starts next Monday."
                }
            ]
            for item in sample_leads:
                db_lead = models.Lead(**item)
                db.add(db_lead)
            db.commit()
            print("[Startup] Database initialized with 12 sample leads.")
    finally:
        if should_close:
            db.close()

# Lifespan handler for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and seed data safely
    try:
        Base.metadata.create_all(bind=engine)
        if is_sqlite and hasattr(engine.url, "database") and engine.url.database:
            try:
                migrate_db.run_migration(engine.url.database)
            except Exception as e:
                print(f"[Startup Warning] SQLite migration skipped/failed: {e}")
        seed_sample_leads()
        print("[Startup] Database tables initialized and verified successfully.")
    except Exception as e:
        print(f"[Startup Warning] Database initialization deferred or failed: {e}")
    yield

app = FastAPI(
    title="LeadFlow API",
    description="FastAPI Backend for LeadFlow CRM & Follow-up Tracker",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = [
    "https://lead-flow-acme-7c28.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:4173",
    "http://localhost:5178",
"http://127.0.0.1:5178",
]
env_origins = os.environ.get("ALLOWED_ORIGINS")
if env_origins:
    for orig in env_origins.split(","):
        cleaned = orig.strip()
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Root & Health Endpoints
# -----------------------------------------------------------------------------
@app.get("/")
def root_endpoint():
    return {
        "status": "ok",
        "app": "LeadFlow API",
        "version": "1.0.0",
        "health": "/api/health",
        "docs": "/docs"
    }

@app.get("/health")
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    db_type = "sqlite" if is_sqlite else "postgresql"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok" if "unhealthy" not in db_status else "degraded",
        "app": "LeadFlow API",
        "database": db_type,
        "database_status": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

VALID_STATUSES = {"new": "New", "contacted": "Contacted", "meeting": "Meeting", "won": "Won", "lost": "Lost"}

# -----------------------------------------------------------------------------
# GET /api/stats
# -----------------------------------------------------------------------------
@app.get("/api/stats", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    leads = db.query(models.Lead).all()
    today_str = date.today().strftime("%Y-%m-%d")

    total_leads = len(leads)
    contacted = sum(1 for l in leads if l.status == "Contacted")
    meetings = sum(1 for l in leads if l.status == "Meeting")
    won_leads = sum(1 for l in leads if l.status == "Won")
    lost_leads = sum(1 for l in leads if l.status == "Lost")
    new_leads = sum(1 for l in leads if l.status == "New")

    pipeline_val = sum((l.deal_value or 0.0) for l in leads if l.status != "Lost")
    win_rate = round((won_leads / total_leads * 100)) if total_leads > 0 else 0

    overdue = 0
    due_today = 0
    upcoming = 0

    for l in leads:
        if l.status not in ["Won", "Lost"] and l.follow_up_date:
            if l.follow_up_date < today_str:
                overdue += 1
            elif l.follow_up_date == today_str:
                due_today += 1
            else:
                upcoming += 1

    return schemas.StatsResponse(
        total_leads=total_leads,
        contacted=contacted,
        meetings=meetings,
        won_leads=won_leads,
        lost_leads=lost_leads,
        new_leads=new_leads,
        pipeline_value=pipeline_val,
        win_rate=win_rate,
        overdue_leads=overdue,
        due_today_leads=due_today,
        upcoming_leads=upcoming
    )

# -----------------------------------------------------------------------------
# GET /api/leads
# -----------------------------------------------------------------------------
@app.get("/api/leads", response_model=List[schemas.LeadResponse])
def get_leads(
    search: Optional[str] = Query(None, description="Search company, contact, or city"),
    status: Optional[str] = Query(None, description="Filter by status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    urgency: Optional[str] = Query(None, description="Filter by urgency: overdue, today, upcoming"),
    sort_by: Optional[str] = Query(None, alias="sortBy", description="Sort field: companyName, dealValue, followUpDate, id"),
    sort_order: Optional[str] = Query("desc", alias="sortOrder", description="Sort order: asc, desc"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Lead)

    if status and status.upper() != "ALL":
        query = query.filter(models.Lead.status.ilike(status.strip()))

    if city and city.upper() != "ALL":
        query = query.filter(models.Lead.city.ilike(city.strip()))

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                models.Lead.company_name.ilike(term),
                models.Lead.contact_person.ilike(term),
                models.Lead.city.ilike(term),
                models.Lead.email.ilike(term)
            )
        )

    if urgency and urgency.upper() != "ALL":
        today_str = date.today().strftime("%Y-%m-%d")
        if urgency.lower() == "overdue":
            query = query.filter(
                models.Lead.follow_up_date < today_str,
                models.Lead.status.notin_(["Won", "Lost"])
            )
        elif urgency.lower() == "today":
            query = query.filter(
                models.Lead.follow_up_date == today_str,
                models.Lead.status.notin_(["Won", "Lost"])
            )
        elif urgency.lower() == "upcoming":
            query = query.filter(
                models.Lead.follow_up_date > today_str,
                models.Lead.status.notin_(["Won", "Lost"])
            )

    sort_field_map = {
        "dealvalue": models.Lead.deal_value,
        "deal_value": models.Lead.deal_value,
        "companyname": models.Lead.company_name,
        "company_name": models.Lead.company_name,
        "contactperson": models.Lead.contact_person,
        "contact_person": models.Lead.contact_person,
        "followupdate": models.Lead.follow_up_date,
        "follow_up_date": models.Lead.follow_up_date,
        "status": models.Lead.status,
        "city": models.Lead.city,
        "createdat": models.Lead.created_at,
        "created_at": models.Lead.created_at,
        "updatedat": models.Lead.updated_at,
        "updated_at": models.Lead.updated_at,
        "id": models.Lead.id
    }

    if sort_by and sort_by.lower() in sort_field_map:
        target_col = sort_field_map[sort_by.lower()]
        if sort_order and sort_order.lower() == "asc":
            query = query.order_by(asc(target_col))
        else:
            query = query.order_by(desc(target_col))
    else:
        query = query.order_by(desc(models.Lead.id))

    leads = query.all()
    return leads

# -----------------------------------------------------------------------------
# GET /api/leads/{id}
# -----------------------------------------------------------------------------
@app.get("/api/leads/{lead_id}", response_model=schemas.LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return lead

# -----------------------------------------------------------------------------
# POST /api/leads
# -----------------------------------------------------------------------------
@app.post("/api/leads", response_model=schemas.LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(lead_in: schemas.LeadCreate, db: Session = Depends(get_db)):
    # Validate required fields
    if not lead_in.company_name or not lead_in.company_name.strip():
        raise HTTPException(status_code=400, detail="Company name is required and cannot be empty")
    if not lead_in.follow_up_date or not lead_in.follow_up_date.strip():
        raise HTTPException(status_code=400, detail="Follow-up date is required")

    email_val = (lead_in.email or "").strip()
    if email_val and ("@" not in email_val or "." not in email_val):
        raise HTTPException(status_code=400, detail="Invalid email address format")

    # Deal value cannot be negative
    deal_val = float(lead_in.deal_value or 0.0)
    if deal_val < 0:
        raise HTTPException(status_code=400, detail="Deal value cannot be negative")

    # Normalize status
    norm_status = VALID_STATUSES.get((lead_in.status or "New").strip().lower(), "New")

    now = datetime.utcnow()
    new_lead = models.Lead(
        company_name=lead_in.company_name.strip(),
        contact_person=(lead_in.contact_person or "").strip(),
        email=email_val,
        phone=(lead_in.phone or "").strip(),
        city=normalize_city_name(lead_in.city or "Unknown"),
        status=norm_status,
        follow_up_date=lead_in.follow_up_date.strip(),
        deal_value=deal_val,
        notes=(lead_in.notes or "").strip(),
        created_at=now,
        updated_at=now
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead

# -----------------------------------------------------------------------------
# PUT /api/leads/{id}
# -----------------------------------------------------------------------------
@app.put("/api/leads/{lead_id}", response_model=schemas.LeadResponse)
def update_lead(lead_id: int, lead_update: schemas.LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )

    update_data = lead_update.model_dump(exclude_unset=True)

    if "company_name" in update_data and update_data["company_name"] is not None:
        val = update_data["company_name"].strip()
        if not val:
            raise HTTPException(status_code=400, detail="Company name cannot be empty")
        lead.company_name = val

    if "contact_person" in update_data and update_data["contact_person"] is not None:
        lead.contact_person = update_data["contact_person"].strip()

    if "email" in update_data and update_data["email"] is not None:
        val = update_data["email"].strip()
        if val and ("@" not in val or "." not in val):
            raise HTTPException(status_code=400, detail="Invalid email address format")
        lead.email = val

    if "phone" in update_data and update_data["phone"] is not None:
        lead.phone = update_data["phone"].strip()

    if "city" in update_data and update_data["city"] is not None:
        val = update_data["city"].strip()
        if not val:
            raise HTTPException(status_code=400, detail="City cannot be empty")
        lead.city = normalize_city_name(val)

    if "status" in update_data and update_data["status"] is not None:
        lead.status = VALID_STATUSES.get(update_data["status"].strip().lower(), lead.status)

    if "follow_up_date" in update_data and update_data["follow_up_date"] is not None:
        val = update_data["follow_up_date"].strip()
        if val:
            lead.follow_up_date = val

    if "deal_value" in update_data and update_data["deal_value"] is not None:
        val = float(update_data["deal_value"])
        if val < 0:
            raise HTTPException(status_code=400, detail="Deal value cannot be negative")
        lead.deal_value = val

    if "notes" in update_data and update_data["notes"] is not None:
        lead.notes = update_data["notes"].strip()

    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return lead

# -----------------------------------------------------------------------------
# DELETE /api/leads/{id}
# -----------------------------------------------------------------------------
@app.delete("/api/leads/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )

    db.delete(lead)
    db.commit()
    return {"message": "Lead deleted successfully", "id": lead_id}

# -----------------------------------------------------------------------------
# POST /api/leads/upload-csv (and alias /api/leads/import-csv)
# -----------------------------------------------------------------------------
@app.post("/api/leads/upload-csv", response_model=schemas.CSVImportResult)
@app.post("/api/leads/import-csv", response_model=schemas.CSVImportResult)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be a CSV file (.csv)"
        )

    contents = await file.read()
    # Decode with fallback for UTF-8-sig or latin-1
    try:
        decoded = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            decoded = contents.decode("utf-8")
        except UnicodeDecodeError:
            decoded = contents.decode("latin-1")

    csv_file = io.StringIO(decoded)
    reader = csv.reader(csv_file)

    try:
        header_row = next(reader)
    except StopIteration:
        raise HTTPException(status_code=400, detail="The CSV file is empty")

    # Normalize header mapping
    header_map = {}
    for idx, col in enumerate(header_row):
        col_clean = col.strip().lower()
        if "company" in col_clean or "organization" in col_clean:
            header_map["company_name"] = idx
        elif "contact" in col_clean or "person" in col_clean or ("name" in col_clean and "company" not in col_clean):
            header_map["contact_person"] = idx
        elif "email" in col_clean or "mail" in col_clean:
            header_map["email"] = idx
        elif "phone" in col_clean or "mobile" in col_clean or "tel" in col_clean:
            header_map["phone"] = idx
        elif "city" in col_clean or "location" in col_clean or "town" in col_clean:
            header_map["city"] = idx
        elif "status" in col_clean or "stage" in col_clean:
            header_map["status"] = idx
        elif "follow" in col_clean or "iso" in col_clean:
            header_map["follow_up_date"] = idx
        elif "date" in col_clean and "created" not in col_clean:
            if "follow_up_date" not in header_map:
                header_map["follow_up_date"] = idx
        elif "value" in col_clean or "deal" in col_clean or "amount" in col_clean:
            header_map["deal_value"] = idx
        elif "notes" in col_clean or "note" in col_clean or "comment" in col_clean or "description" in col_clean:
            header_map["notes"] = idx

    # Verify essential columns
    missing_cols = []
    if "company_name" not in header_map:
        missing_cols.append("Company Name")
    if "contact_person" not in header_map:
        missing_cols.append("Contact Person")
    if "email" not in header_map:
        missing_cols.append("Email")

    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns: {', '.join(missing_cols)}"
        )

    imported_count = 0
    skipped_count = 0
    errors = []
    row_idx = 1  # 1-indexed (header was row 1)

    default_follow_up = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        now = datetime.utcnow()
        for row in reader:
            row_idx += 1
            # Skip completely empty rows
            if not row or all(not cell.strip() for cell in row):
                continue

            def get_val(key, default=""):
                idx = header_map.get(key)
                if idx is not None and idx < len(row):
                    return row[idx].strip()
                return default

            comp = get_val("company_name")
            contact = get_val("contact_person")
            email_val = get_val("email")
            phone_val = get_val("phone", "+1 (555) 000-0000")
            city_val = get_val("city", "Unknown")
            status_val = get_val("status", "New")
            date_val = get_val("follow_up_date", default_follow_up)
            val_str = get_val("deal_value", "0")
            notes_val = get_val("notes", "")

            # Row validation
            if not comp:
                errors.append(f"Row {row_idx}: Missing Company Name")
                skipped_count += 1
                continue
            if not contact:
                errors.append(f"Row {row_idx} ({comp}): Missing Contact Person")
                skipped_count += 1
                continue
            if not email_val or "@" not in email_val:
                errors.append(f"Row {row_idx} ({comp}): Invalid or missing email '{email_val}'")
                skipped_count += 1
                continue

            # Clean deal value
            try:
                cleaned_val = val_str.replace("$", "").replace(",", "").strip()
                deal_val_num = float(cleaned_val) if cleaned_val else 0.0
            except ValueError:
                deal_val_num = 0.0

            # Normalize status
            valid_statuses = ["New", "Contacted", "Meeting", "Won", "Lost"]
            matched_status = next((s for s in valid_statuses if s.lower() == status_val.lower()), "New")

            # Normalize date
            if not date_val or len(date_val) < 8:
                date_val = default_follow_up

            new_lead = models.Lead(
                company_name=comp,
                contact_person=contact,
                email=email_val,
                phone=phone_val,
                city=normalize_city_name(city_val),
                status=matched_status,
                follow_up_date=date_val,
                deal_value=max(0.0, deal_val_num),
                notes=notes_val,
                created_at=now,
                updated_at=now
            )
            db.add(new_lead)
            imported_count += 1

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error during CSV import transaction: {str(e)}"
        )

    total_processed = imported_count + skipped_count
    msg = f"Successfully imported {imported_count} leads."
    if skipped_count > 0:
        msg += f" {skipped_count} rows were skipped due to errors."

    return schemas.CSVImportResult(
        total_rows=total_processed,
        imported_count=imported_count,
        skipped_count=skipped_count,
        errors=errors[:20],  # Return up to 20 errors for display
        message=msg
    )

# -----------------------------------------------------------------------------
# POST /api/leads/reset-sample
# -----------------------------------------------------------------------------
@app.post("/api/leads/reset-sample")
def reset_sample_leads_endpoint(db: Session = Depends(get_db)):
    # Safeguard against accidental data wipes in production
    if os.environ.get("ENV") == "production" and os.environ.get("ALLOW_RESET") != "true":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reset sample data is disabled in production environments."
        )
    db.query(models.Lead).delete()
    db.commit()
    seed_sample_leads(db)
    new_count = db.query(models.Lead).count()
    return {"message": "Database reset to initial sample leads successfully", "count": new_count}

# -----------------------------------------------------------------------------
# Email / Notifications Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/email/status")
def get_email_status_endpoint():
    """
    Returns public, safe email configuration status for the UI.
    Never exposes passwords, tokens, or credentials.
    """
    return email_service.get_safe_email_status()

@app.post("/api/email/send-test")
def send_test_email_endpoint():
    """
    Sends a test email to the configured administrator address (FOLLOWUP_EMAIL_TO)
    to verify SMTP configuration. Does NOT record into daily_email_logs.
    """
    result = email_service.send_test_email()
    if result.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to deliver test email.")
        )
    return result

@app.post("/api/cron/daily-followup")
def cron_daily_followup_endpoint(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Protected cron endpoint executed daily at 8:00 AM Asia/Kolkata by external scheduler.
    Requires header: Authorization: Bearer <CRON_SECRET>
    Executes idempotently and records delivery status into daily_email_logs.
    """
    config = email_service.get_email_config()
    expected_secret = config.get("cron_secret", "")

    if not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cron secret is not configured on the server (CRON_SECRET)."
        )

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header."
        )

    parts = authorization.strip().split()
    token = parts[1] if (len(parts) == 2 and parts[0].lower() == "bearer") else parts[0]

    if token != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron authorization token."
        )

    result = email_service.send_daily_followup_email(db)
    if result.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Daily follow-up email delivery failed.")
        )

    return result

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
