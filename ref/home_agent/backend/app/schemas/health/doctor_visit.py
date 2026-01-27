from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class VisitType(str, Enum):
    ROUTINE_CHECKUP = "routine_checkup"
    FOLLOW_UP = "follow_up"
    SPECIALIST = "specialist"
    EMERGENCY = "emergency"
    VACCINATION = "vaccination"
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"

class DoctorVisitBase(BaseModel):
    doctor_name: str = Field(..., min_length=2, max_length=100)
    specialty: Optional[str] = Field(None, max_length=100)
    visit_type: VisitType
    date: datetime
    duration_minutes: Optional[int] = Field(None, gt=0, lt=480)  # Max 8 hours
    reason: str = Field(..., min_length=3)
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    notes: Optional[str] = None
    follow_up_needed: bool = False
    follow_up_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)

    @validator('follow_up_date')
    def validate_follow_up_date(cls, v, values):
        if v and 'date' in values and v <= values['date']:
            raise ValueError("Follow-up date must be after visit date")
        return v

class DoctorVisitCreate(DoctorVisitBase):
    pass

class DoctorVisitUpdate(BaseModel):
    doctor_name: Optional[str] = Field(None, min_length=2, max_length=100)
    specialty: Optional[str] = Field(None, max_length=100)
    visit_type: Optional[VisitType] = None
    date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0, lt=480)
    reason: Optional[str] = Field(None, min_length=3)
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    notes: Optional[str] = None
    follow_up_needed: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)

    @validator('follow_up_date')
    def validate_follow_up_date(cls, v, values):
        if v and 'date' in values and values['date'] and v <= values['date']:
            raise ValueError("Follow-up date must be after visit date")
        return v

class DoctorVisitInDBBase(DoctorVisitBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DoctorVisit(DoctorVisitInDBBase):
    pass

class DoctorVisitStats(BaseModel):
    total_visits: int
    visits_by_type: dict[VisitType, int]
    upcoming_visits: List[DoctorVisit]
    recent_visits: List[DoctorVisit]
    pending_follow_ups: List[DoctorVisit] 