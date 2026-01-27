from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date

from .....core.database import get_db
from .....services.health.doctor_visit import DoctorVisitService
from .....schemas.health.doctor_visit import (
    DoctorVisit,
    DoctorVisitCreate,
    DoctorVisitUpdate,
    DoctorVisitStats,
    VisitType
)
from ....dependencies.auth import get_current_user
from .....schemas.user import User

router = APIRouter()

@router.get("/", response_model=List[DoctorVisit])
def get_doctor_visits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve doctor visits for the current user.
    """
    visits = DoctorVisitService.get_doctor_visits(db, current_user.id, skip, limit)
    return visits

@router.post("/", response_model=DoctorVisit)
def create_doctor_visit(
    *,
    visit_in: DoctorVisitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new doctor visit record.
    """
    visit = DoctorVisitService.create_doctor_visit(db, current_user.id, visit_in)
    return visit

@router.get("/{visit_id}", response_model=DoctorVisit)
def get_doctor_visit(
    visit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific doctor visit by ID.
    """
    visit = DoctorVisitService.get_doctor_visit(db, current_user.id, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Doctor visit not found")
    return visit

@router.put("/{visit_id}", response_model=DoctorVisit)
def update_doctor_visit(
    *,
    visit_id: int,
    visit_in: DoctorVisitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update doctor visit record.
    """
    visit = DoctorVisitService.update_doctor_visit(
        db, current_user.id, visit_id, visit_in
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Doctor visit not found")
    return visit

@router.delete("/{visit_id}")
def delete_doctor_visit(
    visit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete doctor visit record.
    """
    success = DoctorVisitService.delete_doctor_visit(db, current_user.id, visit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Doctor visit not found")
    return {"message": "Visit record successfully deleted"}

@router.get("/stats/summary", response_model=DoctorVisitStats)
def get_doctor_visit_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get comprehensive statistics about doctor visits.
    Includes total visits, visits by type, upcoming visits, and follow-ups.
    """
    stats = DoctorVisitService.get_doctor_visit_stats(db, current_user.id)
    return stats

@router.get("/search/by-date", response_model=List[DoctorVisit])
def get_visits_by_date_range(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Search visits within a specific date range.
    """
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    visits = DoctorVisitService.get_visits_by_date_range(
        db, current_user.id, start_datetime, end_datetime
    )
    return visits

@router.get("/search/by-doctor", response_model=List[DoctorVisit])
def get_visits_by_doctor(
    doctor_name: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Search visits by doctor name (partial match supported).
    """
    visits = DoctorVisitService.get_visits_by_doctor(
        db, current_user.id, doctor_name
    )
    return visits 