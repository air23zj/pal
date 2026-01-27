from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .....core.database import get_db
from .....services.health.height import HeightService
from .....schemas.health.height import (
    HeightRecord,
    HeightRecordCreate,
    HeightRecordUpdate,
    HeightStats,
    MeasurementUnit
)
from ....dependencies.auth import get_current_user
from .....schemas.user import User

router = APIRouter()

@router.get("/", response_model=List[HeightRecord])
def get_height_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve height records for the current user.
    """
    records = HeightService.get_height_records(db, current_user.id, skip, limit)
    return records

@router.post("/", response_model=HeightRecord)
def create_height_record(
    *,
    record_in: HeightRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new height record.
    """
    record = HeightService.create_height_record(db, current_user.id, record_in)
    return record

@router.get("/{record_id}", response_model=HeightRecord)
def get_height_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific height record by ID.
    """
    record = HeightService.get_height_record(db, current_user.id, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Height record not found")
    return record

@router.put("/{record_id}", response_model=HeightRecord)
def update_height_record(
    *,
    record_id: int,
    record_in: HeightRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update height record.
    """
    record = HeightService.update_height_record(
        db, current_user.id, record_id, record_in
    )
    if not record:
        raise HTTPException(status_code=404, detail="Height record not found")
    return record

@router.delete("/{record_id}")
def delete_height_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete height record.
    """
    success = HeightService.delete_height_record(db, current_user.id, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Height record not found")
    return {"message": "Record successfully deleted"}

@router.get("/stats/summary", response_model=HeightStats)
def get_height_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get height statistics and growth analysis.
    Includes latest height, history count, and growth rate if multiple records exist.
    """
    try:
        stats = HeightService.get_height_stats(db, current_user.id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/convert")
def convert_height(
    height: float = Query(..., gt=0),
    from_unit: MeasurementUnit = Query(...),
    to_unit: MeasurementUnit = Query(...)
) -> Any:
    """
    Convert height between different units (cm/inches).
    """
    try:
        converted_height = HeightService.convert_height(height, from_unit, to_unit)
        return {
            "original_height": height,
            "original_unit": from_unit,
            "converted_height": round(converted_height, 2),
            "converted_unit": to_unit
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 