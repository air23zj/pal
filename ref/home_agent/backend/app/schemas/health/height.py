from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from enum import Enum

class MeasurementUnit(str, Enum):
    CM = "cm"
    INCHES = "inches"

class HeightRecordBase(BaseModel):
    height: float = Field(..., gt=0, lt=300)  # Max height in cm
    unit: MeasurementUnit = Field(default=MeasurementUnit.CM)
    date: datetime = Field(default_factory=datetime.utcnow)
    measured_by: Optional[str] = None
    notes: Optional[str] = None

    @validator('height')
    def validate_height(cls, v, values):
        if 'unit' in values:
            if values['unit'] == MeasurementUnit.CM and (v < 30 or v > 300):
                raise ValueError("Height in cm must be between 30 and 300")
            elif values['unit'] == MeasurementUnit.INCHES and (v < 12 or v > 120):
                raise ValueError("Height in inches must be between 12 and 120")
        return v

class HeightRecordCreate(HeightRecordBase):
    pass

class HeightRecordUpdate(BaseModel):
    height: Optional[float] = Field(None, gt=0, lt=300)
    unit: Optional[MeasurementUnit] = None
    date: Optional[datetime] = None
    measured_by: Optional[str] = None
    notes: Optional[str] = None

    @validator('height')
    def validate_height(cls, v, values):
        if v is not None and 'unit' in values and values['unit'] is not None:
            if values['unit'] == MeasurementUnit.CM and (v < 30 or v > 300):
                raise ValueError("Height in cm must be between 30 and 300")
            elif values['unit'] == MeasurementUnit.INCHES and (v < 12 or v > 120):
                raise ValueError("Height in inches must be between 12 and 120")
        return v

class HeightRecordInDBBase(HeightRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class HeightRecord(HeightRecordInDBBase):
    pass

class HeightStats(BaseModel):
    latest_height: float
    latest_unit: MeasurementUnit
    latest_date: datetime
    history_count: int
    growth_rate: Optional[float] = None  # Change in height per year if multiple records exist 