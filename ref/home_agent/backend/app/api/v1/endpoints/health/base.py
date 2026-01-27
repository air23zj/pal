from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ....core.database import get_db
from ....core.security import get_current_user
from ....models.user import User
from ....services.health.base import HealthService
from ....schemas.health.base import (
    WeightRecordCreate,
    WeightRecordResponse,
    HeightRecordCreate,
    HeightRecordResponse,
    BloodPressureRecordCreate,
    BloodPressureRecordResponse,
    HeartRateRecordCreate,
    HeartRateRecordResponse,
    DoctorVisitCreate,
    DoctorVisitResponse,
    ExerciseGoalsCreate,
    ExerciseGoalsResponse,
    DietaryGoalsCreate,
    DietaryGoalsResponse,
    MedicationCreate,
    MedicationResponse,
    HealthSummary
)

router = APIRouter()

# Weight Records
@router.post("/weight", response_model=WeightRecordResponse)
async def create_weight_record(
    record: WeightRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new weight record."""
    service = HealthService(db)
    return service.create_weight_record(current_user.id, record)

@router.get("/weight", response_model=List[WeightRecordResponse])
async def get_weight_records(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weight records."""
    service = HealthService(db)
    return service.get_weight_records(current_user.id, skip, limit)

# Height Records
@router.post("/height", response_model=HeightRecordResponse)
async def create_height_record(
    record: HeightRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new height record."""
    service = HealthService(db)
    return service.create_height_record(current_user.id, record)

@router.get("/height", response_model=List[HeightRecordResponse])
async def get_height_records(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get height records."""
    service = HealthService(db)
    return service.get_height_records(current_user.id, skip, limit)

# Blood Pressure Records
@router.post("/blood-pressure", response_model=BloodPressureRecordResponse)
async def create_blood_pressure_record(
    record: BloodPressureRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new blood pressure record."""
    service = HealthService(db)
    return service.create_blood_pressure_record(current_user.id, record)

@router.get("/blood-pressure", response_model=List[BloodPressureRecordResponse])
async def get_blood_pressure_records(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get blood pressure records."""
    service = HealthService(db)
    return service.get_blood_pressure_records(current_user.id, skip, limit)

# Heart Rate Records
@router.post("/heart-rate", response_model=HeartRateRecordResponse)
async def create_heart_rate_record(
    record: HeartRateRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new heart rate record."""
    service = HealthService(db)
    return service.create_heart_rate_record(current_user.id, record)

@router.get("/heart-rate", response_model=List[HeartRateRecordResponse])
async def get_heart_rate_records(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get heart rate records."""
    service = HealthService(db)
    return service.get_heart_rate_records(current_user.id, skip, limit)

# Doctor Visits
@router.post("/doctor-visits", response_model=DoctorVisitResponse)
async def create_doctor_visit(
    visit: DoctorVisitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new doctor visit."""
    service = HealthService(db)
    return service.create_doctor_visit(current_user.id, visit)

@router.get("/doctor-visits", response_model=List[DoctorVisitResponse])
async def get_doctor_visits(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get doctor visits."""
    service = HealthService(db)
    return service.get_doctor_visits(current_user.id, skip, limit)

@router.get("/doctor-visits/upcoming", response_model=List[DoctorVisitResponse])
async def get_upcoming_doctor_visits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get upcoming doctor visits."""
    service = HealthService(db)
    return service.get_upcoming_doctor_visits(current_user.id)

# Exercise Goals
@router.post("/exercise-goals", response_model=ExerciseGoalsResponse)
async def create_or_update_exercise_goals(
    goals: ExerciseGoalsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update exercise goals."""
    service = HealthService(db)
    return service.create_or_update_exercise_goals(current_user.id, goals)

@router.get("/exercise-goals", response_model=ExerciseGoalsResponse)
async def get_exercise_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get exercise goals."""
    service = HealthService(db)
    return service.get_exercise_goals(current_user.id)

# Dietary Goals
@router.post("/dietary-goals", response_model=DietaryGoalsResponse)
async def create_or_update_dietary_goals(
    goals: DietaryGoalsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update dietary goals."""
    service = HealthService(db)
    return service.create_or_update_dietary_goals(current_user.id, goals)

@router.get("/dietary-goals", response_model=DietaryGoalsResponse)
async def get_dietary_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dietary goals."""
    service = HealthService(db)
    return service.get_dietary_goals(current_user.id)

# Medications
@router.post("/medications", response_model=MedicationResponse)
async def create_medication(
    medication: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new medication."""
    service = HealthService(db)
    return service.create_medication(current_user.id, medication)

@router.get("/medications", response_model=List[MedicationResponse])
async def get_medications(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get medications."""
    service = HealthService(db)
    return service.get_medications(current_user.id, active_only)

@router.put("/medications/{medication_id}/status")
async def update_medication_status(
    medication_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update medication status."""
    service = HealthService(db)
    return service.update_medication(medication_id, current_user.id, is_active)

# Health Summary
@router.get("/summary", response_model=HealthSummary)
async def get_health_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health summary."""
    service = HealthService(db)
    return service.get_health_summary(current_user.id) 