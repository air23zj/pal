from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BloodPressureRecordBase(BaseModel):
    systolic: int = Field(..., gt=50, lt=250)
    diastolic: int = Field(..., gt=30, lt=200)
    pulse: Optional[int] = Field(None, gt=30, lt=220)
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class BloodPressureRecordCreate(BloodPressureRecordBase):
    pass

class BloodPressureRecordUpdate(BaseModel):
    systolic: Optional[int] = Field(None, gt=50, lt=250)
    diastolic: Optional[int] = Field(None, gt=30, lt=200)
    pulse: Optional[int] = Field(None, gt=30, lt=220)
    date: Optional[datetime] = None
    notes: Optional[str] = None

class BloodPressureRecordInDBBase(BloodPressureRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class BloodPressureRecord(BloodPressureRecordInDBBase):
    pass 