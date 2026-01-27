from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class ActivityLevel(str, Enum):
    RESTING = "resting"
    LIGHT = "light"
    MODERATE = "moderate"
    VIGOROUS = "vigorous"

class HeartRateRecordBase(BaseModel):
    heart_rate: int = Field(..., gt=20, lt=250)  # Normal human heart rate range
    activity_level: Optional[ActivityLevel] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class HeartRateRecordCreate(HeartRateRecordBase):
    pass

class HeartRateRecordUpdate(BaseModel):
    heart_rate: Optional[int] = Field(None, gt=20, lt=250)
    activity_level: Optional[ActivityLevel] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None

class HeartRateRecordInDBBase(HeartRateRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class HeartRateRecord(HeartRateRecordInDBBase):
    pass

class HeartRateStats(BaseModel):
    average: float
    maximum: int
    minimum: int
    resting_average: Optional[float] = None
    by_activity_level: dict[ActivityLevel, Optional[float]] = Field(default_factory=dict) 