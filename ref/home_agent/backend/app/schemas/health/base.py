from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class WeightRecordBase(BaseModel):
    weight: float = Field(..., gt=0, description="Weight in kilograms")
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class WeightRecordCreate(WeightRecordBase):
    pass

class WeightRecordResponse(WeightRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class HeightRecordBase(BaseModel):
    height: float = Field(..., gt=0, description="Height in centimeters")
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class HeightRecordCreate(HeightRecordBase):
    pass

class HeightRecordResponse(HeightRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class BloodPressureRecordBase(BaseModel):
    systolic: int = Field(..., gt=0, description="Systolic pressure in mmHg")
    diastolic: int = Field(..., gt=0, description="Diastolic pressure in mmHg")
    pulse: int = Field(..., gt=0, description="Pulse rate in bpm")
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class BloodPressureRecordCreate(BloodPressureRecordBase):
    pass

class BloodPressureRecordResponse(BloodPressureRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class HeartRateRecordBase(BaseModel):
    heart_rate: int = Field(..., gt=0, description="Heart rate in bpm")
    date: datetime = Field(default_factory=datetime.utcnow)
    activity_type: Optional[str] = None
    notes: Optional[str] = None

class HeartRateRecordCreate(HeartRateRecordBase):
    pass

class HeartRateRecordResponse(HeartRateRecordBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class DoctorVisitBase(BaseModel):
    doctor_name: str
    specialty: str
    date: datetime
    reason: str
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None

class DoctorVisitCreate(DoctorVisitBase):
    pass

class DoctorVisitResponse(DoctorVisitBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class ExerciseGoalsBase(BaseModel):
    daily_steps: int = Field(..., ge=0)
    weekly_exercise_minutes: int = Field(..., ge=0)
    target_heart_rate: Optional[int] = Field(None, gt=0)
    preferred_activities: Optional[str] = None

class ExerciseGoalsCreate(ExerciseGoalsBase):
    pass

class ExerciseGoalsResponse(ExerciseGoalsBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class DietaryGoalsBase(BaseModel):
    daily_calories: int = Field(..., gt=0)
    protein_grams: int = Field(..., ge=0)
    carbs_grams: int = Field(..., ge=0)
    fat_grams: int = Field(..., ge=0)
    water_liters: float = Field(..., ge=0)
    restrictions: Optional[str] = None

class DietaryGoalsCreate(DietaryGoalsBase):
    pass

class DietaryGoalsResponse(DietaryGoalsBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class MedicationBase(BaseModel):
    name: str
    dosage: str
    frequency: str
    start_date: datetime
    end_date: Optional[datetime] = None
    prescribing_doctor: str
    notes: Optional[str] = None
    is_active: bool = True

class MedicationCreate(MedicationBase):
    pass

class MedicationResponse(MedicationBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

# Aggregate Response Models
class HealthSummary(BaseModel):
    latest_weight: Optional[WeightRecordResponse] = None
    latest_height: Optional[HeightRecordResponse] = None
    latest_blood_pressure: Optional[BloodPressureRecordResponse] = None
    latest_heart_rate: Optional[HeartRateRecordResponse] = None
    upcoming_doctor_visits: List[DoctorVisitResponse] = []
    exercise_goals: Optional[ExerciseGoalsResponse] = None
    dietary_goals: Optional[DietaryGoalsResponse] = None
    active_medications: List[MedicationResponse] = [] 