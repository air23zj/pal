from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .....core.database import get_db
from .....services.health.blood_pressure import BloodPressureService
from .....schemas.health.blood_pressure import (
    BloodPressureRecord,
    BloodPressureRecordCreate,
    BloodPressureRecordUpdate
)
from ....dependencies.auth import get_current_user
from .....schemas.user import User

router = APIRouter()

@router.get("/", response_model=List[BloodPressureRecord])
def get_blood_pressure_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve blood pressure records for the current user.
    """
    records = BloodPressureService.get_blood_pressure_records(db, current_user.id, skip, limit)
    return records

@router.post("/", response_model=BloodPressureRecord)
def create_blood_pressure_record(
    *,
    record_in: BloodPressureRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new blood pressure record.
    """
    record = BloodPressureService.create_blood_pressure_record(db, current_user.id, record_in)
    return record

@router.get("/{record_id}", response_model=BloodPressureRecord)
def get_blood_pressure_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific blood pressure record by ID.
    """
    record = BloodPressureService.get_blood_pressure_record(db, current_user.id, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Blood pressure record not found")
    return record

@router.put("/{record_id}", response_model=BloodPressureRecord)
def update_blood_pressure_record(
    *,
    record_id: int,
    record_in: BloodPressureRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update blood pressure record.
    """
    record = BloodPressureService.update_blood_pressure_record(
        db, current_user.id, record_id, record_in
    )
    if not record:
        raise HTTPException(status_code=404, detail="Blood pressure record not found")
    return record

@router.delete("/{record_id}")
def delete_blood_pressure_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete blood pressure record.
    """
    success = BloodPressureService.delete_blood_pressure_record(db, current_user.id, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Blood pressure record not found")
    return {"message": "Record successfully deleted"}

@router.get("/trend/{days}", response_model=List[BloodPressureRecord])
def get_blood_pressure_trend(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get blood pressure trend over specified number of days.
    """
    records = BloodPressureService.get_blood_pressure_trend(db, current_user.id, days)
    return records

@router.get("/stats/{days}", response_model=Dict)
def get_blood_pressure_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get blood pressure statistics over specified number of days.
    """
    stats = BloodPressureService.get_blood_pressure_stats(db, current_user.id, days)
    return stats 