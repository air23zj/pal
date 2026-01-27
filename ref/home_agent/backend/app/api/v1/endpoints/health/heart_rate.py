from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .....core.database import get_db
from .....services.health.heart_rate import HeartRateService
from .....schemas.health.heart_rate import (
    HeartRateRecord,
    HeartRateRecordCreate,
    HeartRateRecordUpdate,
    HeartRateStats
)
from ....dependencies.auth import get_current_user
from .....schemas.user import User

router = APIRouter()

@router.get("/", response_model=List[HeartRateRecord])
def get_heart_rate_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve heart rate records for the current user.
    """
    records = HeartRateService.get_heart_rate_records(db, current_user.id, skip, limit)
    return records

@router.post("/", response_model=HeartRateRecord)
def create_heart_rate_record(
    *,
    record_in: HeartRateRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new heart rate record.
    """
    record = HeartRateService.create_heart_rate_record(db, current_user.id, record_in)
    return record

@router.get("/{record_id}", response_model=HeartRateRecord)
def get_heart_rate_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific heart rate record by ID.
    """
    record = HeartRateService.get_heart_rate_record(db, current_user.id, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Heart rate record not found")
    return record

@router.put("/{record_id}", response_model=HeartRateRecord)
def update_heart_rate_record(
    *,
    record_id: int,
    record_in: HeartRateRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update heart rate record.
    """
    record = HeartRateService.update_heart_rate_record(
        db, current_user.id, record_id, record_in
    )
    if not record:
        raise HTTPException(status_code=404, detail="Heart rate record not found")
    return record

@router.delete("/{record_id}")
def delete_heart_rate_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete heart rate record.
    """
    success = HeartRateService.delete_heart_rate_record(db, current_user.id, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Heart rate record not found")
    return {"message": "Record successfully deleted"}

@router.get("/trend/{days}", response_model=List[HeartRateRecord])
def get_heart_rate_trend(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get heart rate trend over specified number of days.
    """
    records = HeartRateService.get_heart_rate_trend(db, current_user.id, days)
    return records

@router.get("/stats/{days}", response_model=HeartRateStats)
def get_heart_rate_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get heart rate statistics over specified number of days.
    Includes overall stats and breakdowns by activity level.
    """
    stats = HeartRateService.get_heart_rate_stats(db, current_user.id, days)
    return stats 