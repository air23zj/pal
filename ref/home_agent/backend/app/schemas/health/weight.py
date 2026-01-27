from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class WeightRecordBase(BaseModel):
    weight: float = Field(..., gt=0, lt=1000)  # Weight in kg/lbs
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class WeightRecordCreate(WeightRecordBase):
    pass

class WeightRecordUpdate(BaseModel):
    weight: Optional[float] = Field(None, gt=0, lt=1000)
    date: Optional[datetime] = None
    notes: Optional[str] = None

class WeightRecordInDBBase(WeightRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class WeightRecord(WeightRecordInDBBase):
    pass 