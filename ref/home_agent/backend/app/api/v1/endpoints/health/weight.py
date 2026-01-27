from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .....core.database import get_db
from .....services.health.weight import WeightService
from .....schemas.health.weight import WeightRecord, WeightRecordCreate, WeightRecordUpdate
from ....dependencies.auth import get_current_user
from .....schemas.user import User

router = APIRouter()

@router.get("/", response_model=List[WeightRecord])
def get_weight_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve weight records for the current user.
    """
    records = WeightService.get_weight_records(db, current_user.id, skip, limit)
    return records

@router.post("/", response_model=WeightRecord)
def create_weight_record(
    *,
    record_in: WeightRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new weight record.
    """
    record = WeightService.create_weight_record(db, current_user.id, record_in)
    return record

@router.get("/{record_id}", response_model=WeightRecord)
def get_weight_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific weight record by ID.
    """
    record = WeightService.get_weight_record(db, current_user.id, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weight record not found")
    return record

@router.put("/{record_id}", response_model=WeightRecord)
def update_weight_record(
    *,
    record_id: int,
    record_in: WeightRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update weight record.
    """
    record = WeightService.update_weight_record(db, current_user.id, record_id, record_in)
    if not record:
        raise HTTPException(status_code=404, detail="Weight record not found")
    return record

@router.delete("/{record_id}")
def delete_weight_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete weight record.
    """
    success = WeightService.delete_weight_record(db, current_user.id, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Weight record not found")
    return {"message": "Record successfully deleted"}

@router.get("/trend/{days}", response_model=List[WeightRecord])
def get_weight_trend(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get weight trend over specified number of days.
    """
    records = WeightService.get_weight_trend(db, current_user.id, days)
    return records 