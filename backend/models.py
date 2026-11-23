from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(255), nullable=True, default="", index=True)
    email = Column(String(255), nullable=True, default="", index=True)
    phone = Column(String(50), nullable=True, default="")
    city = Column(String(100), nullable=False, default="Unknown", index=True)
    status = Column(String(50), nullable=False, default="New", index=True)
    follow_up_date = Column(String(50), nullable=False, index=True)  # YYYY-MM-DD
    deal_value = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        created_iso = self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        updated_iso = self.updated_at.isoformat() if self.updated_at else created_iso
        return {
            "id": self.id,
            "company_name": self.company_name,
            "companyName": self.company_name,
            "contact_person": self.contact_person or "",
            "contactPerson": self.contact_person or "",
            "email": self.email or "",
            "phone": self.phone or "",
            "city": self.city or "Unknown",
            "status": self.status,
            "follow_up_date": self.follow_up_date,
            "followUpDate": self.follow_up_date,
            "deal_value": self.deal_value,
            "dealValue": self.deal_value,
            "notes": self.notes or "",
            "created_at": created_iso,
            "createdAt": created_iso,
            "updated_at": updated_iso,
            "updatedAt": updated_iso
        }

class DailyEmailLog(Base):
    __tablename__ = "daily_email_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    delivery_date = Column(String(50), nullable=False, unique=True, index=True)  # YYYY-MM-DD
    recipient = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="SUCCESS", index=True)  # SUCCESS or FAILED
    due_today_count = Column(Integer, nullable=False, default=0)
    overdue_count = Column(Integer, nullable=False, default=0)
    sent_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)

    def to_dict(self):
        sent_iso = self.sent_at.isoformat() if self.sent_at else None
        return {
            "id": self.id,
            "delivery_date": self.delivery_date,
            "deliveryDate": self.delivery_date,
            "recipient": self.recipient,
            "status": self.status,
            "due_today_count": self.due_today_count,
            "dueTodayCount": self.due_today_count,
            "overdue_count": self.overdue_count,
            "overdueCount": self.overdue_count,
            "sent_at": sent_iso,
            "sentAt": sent_iso,
            "error_message": self.error_message,
            "errorMessage": self.error_message
        }
