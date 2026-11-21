from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from typing import Optional, List
from datetime import datetime

VALID_STATUS_LIST = ["New", "Contacted", "Meeting", "Won", "Lost"]

class LeadBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    company_name: str = Field(..., alias="companyName")
    contact_person: Optional[str] = Field(default="", alias="contactPerson")
    email: Optional[str] = ""
    phone: Optional[str] = ""
    city: Optional[str] = "Unknown"
    status: str = "New"
    follow_up_date: str = Field(..., alias="followUpDate")
    deal_value: float = Field(default=0.0, ge=0.0, alias="dealValue")
    notes: Optional[str] = ""

class LeadCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    company_name: str = Field(..., alias="companyName")
    contact_person: Optional[str] = Field(default="", alias="contactPerson")
    email: Optional[str] = ""
    phone: Optional[str] = ""
    city: Optional[str] = "Unknown"
    status: Optional[str] = "New"
    follow_up_date: str = Field(..., alias="followUpDate")
    deal_value: Optional[float] = Field(default=0.0, ge=0.0, alias="dealValue")
    notes: Optional[str] = ""

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Company name cannot be empty or whitespace")
        return v.strip()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if not v:
            return "New"
        v_clean = v.strip().lower()
        mapping = {s.lower(): s for s in VALID_STATUS_LIST}
        if v_clean not in mapping:
            raise ValueError(f"Invalid status '{v}'. Allowed statuses: {', '.join(VALID_STATUS_LIST)}")
        return mapping[v_clean]

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return ""
        v_clean = v.strip()
        if "@" not in v_clean or "." not in v_clean:
            raise ValueError("Invalid email format")
        return v_clean

class LeadUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    company_name: Optional[str] = Field(None, alias="companyName")
    contact_person: Optional[str] = Field(None, alias="contactPerson")
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    follow_up_date: Optional[str] = Field(None, alias="followUpDate")
    deal_value: Optional[float] = Field(None, ge=0.0, alias="dealValue")
    notes: Optional[str] = None

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Company name cannot be empty or whitespace")
        return v.strip() if v is not None else None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip().lower()
            mapping = {s.lower(): s for s in VALID_STATUS_LIST}
            if v_clean not in mapping:
                raise ValueError(f"Invalid status '{v}'. Allowed statuses: {', '.join(VALID_STATUS_LIST)}")
            return mapping[v_clean]
        return None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            v_clean = v.strip()
            if "@" not in v_clean or "." not in v_clean:
                raise ValueError("Invalid email format")
            return v_clean
        return v if v is not None else None

class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    company_name: str
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""
    status: str
    follow_up_date: str
    deal_value: float = 0.0
    notes: Optional[str] = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @computed_field
    @property
    def companyName(self) -> str:
        return self.company_name

    @computed_field
    @property
    def contactPerson(self) -> str:
        return self.contact_person or ""

    @computed_field
    @property
    def followUpDate(self) -> str:
        return self.follow_up_date

    @computed_field
    @property
    def dealValue(self) -> float:
        return self.deal_value

    @computed_field
    @property
    def createdAt(self) -> Optional[str]:
        return self.created_at.isoformat() if self.created_at else None

    @computed_field
    @property
    def updatedAt(self) -> Optional[str]:
        if self.updated_at:
            return self.updated_at.isoformat()
        return self.created_at.isoformat() if self.created_at else None

class StatsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_leads: int
    contacted: int
    meetings: int
    won_leads: int
    lost_leads: int
    new_leads: int
    pipeline_value: float
    win_rate: int
    overdue_leads: int
    due_today_leads: int
    upcoming_leads: int

    @computed_field
    @property
    def totalLeads(self) -> int:
        return self.total_leads

    @computed_field
    @property
    def wonLeads(self) -> int:
        return self.won_leads

    @computed_field
    @property
    def lostLeads(self) -> int:
        return self.lost_leads

    @computed_field
    @property
    def newLeads(self) -> int:
        return self.new_leads

    @computed_field
    @property
    def pipelineValue(self) -> float:
        return self.pipeline_value

    @computed_field
    @property
    def winRate(self) -> int:
        return self.win_rate

    @computed_field
    @property
    def overdueLeads(self) -> int:
        return self.overdue_leads

    @computed_field
    @property
    def dueTodayLeads(self) -> int:
        return self.due_today_leads

    @computed_field
    @property
    def upcomingLeads(self) -> int:
        return self.upcoming_leads

class CSVImportResult(BaseModel):
    total_rows: int
    imported_count: int
    skipped_count: int
    errors: List[str]
    message: str
