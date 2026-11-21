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
