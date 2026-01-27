from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func, and_

from ...models.health.doctor_visit import DoctorVisit, VisitType
from ...schemas.health.doctor_visit import DoctorVisitCreate, DoctorVisitUpdate, DoctorVisitStats

class DoctorVisitService:
    @staticmethod
    def get_doctor_visits(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[DoctorVisit]:
        return db.query(DoctorVisit)\
            .filter(DoctorVisit.owner_id == user_id)\
            .order_by(DoctorVisit.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_doctor_visit(
        db: Session, user_id: int, visit_id: int
    ) -> Optional[DoctorVisit]:
        return db.query(DoctorVisit)\
            .filter(DoctorVisit.owner_id == user_id, DoctorVisit.id == visit_id)\
            .first()

    @staticmethod
    def create_doctor_visit(
        db: Session, user_id: int, visit: DoctorVisitCreate
    ) -> DoctorVisit:
        db_visit = DoctorVisit(**visit.model_dump(), owner_id=user_id)
        db.add(db_visit)
        db.commit()
        db.refresh(db_visit)
        return db_visit

    @staticmethod
    def update_doctor_visit(
        db: Session, user_id: int, visit_id: int, visit: DoctorVisitUpdate
    ) -> Optional[DoctorVisit]:
        db_visit = DoctorVisitService.get_doctor_visit(db, user_id, visit_id)
        if db_visit:
            update_data = visit.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_visit, field, value)
            db.commit()
            db.refresh(db_visit)
        return db_visit

    @staticmethod
    def delete_doctor_visit(
        db: Session, user_id: int, visit_id: int
    ) -> bool:
        db_visit = DoctorVisitService.get_doctor_visit(db, user_id, visit_id)
        if db_visit:
            db.delete(db_visit)
            db.commit()
            return True
        return False

    @staticmethod
    def get_doctor_visit_stats(
        db: Session, user_id: int
    ) -> DoctorVisitStats:
        """Get comprehensive statistics about doctor visits"""
        now = datetime.utcnow()

        # Get total visits
        total_visits = db.query(func.count(DoctorVisit.id))\
            .filter(DoctorVisit.owner_id == user_id)\
            .scalar()

        # Get visits by type
        visits_by_type = {}
        for visit_type in VisitType:
            count = db.query(func.count(DoctorVisit.id))\
                .filter(
                    DoctorVisit.owner_id == user_id,
                    DoctorVisit.visit_type == visit_type
                )\
                .scalar()
            visits_by_type[visit_type] = count

        # Get upcoming visits (next 30 days)
        upcoming_visits = db.query(DoctorVisit)\
            .filter(
                DoctorVisit.owner_id == user_id,
                DoctorVisit.date > now
            )\
            .order_by(DoctorVisit.date.asc())\
            .limit(5)\
            .all()

        # Get recent visits (last 30 days)
        recent_visits = db.query(DoctorVisit)\
            .filter(
                DoctorVisit.owner_id == user_id,
                DoctorVisit.date <= now,
                DoctorVisit.date > now - timedelta(days=30)
            )\
            .order_by(DoctorVisit.date.desc())\
            .all()

        # Get pending follow-ups
        pending_follow_ups = db.query(DoctorVisit)\
            .filter(
                DoctorVisit.owner_id == user_id,
                DoctorVisit.follow_up_needed == True,
                DoctorVisit.follow_up_date > now
            )\
            .order_by(DoctorVisit.follow_up_date.asc())\
            .all()

        return DoctorVisitStats(
            total_visits=total_visits,
            visits_by_type=visits_by_type,
            upcoming_visits=upcoming_visits,
            recent_visits=recent_visits,
            pending_follow_ups=pending_follow_ups
        )

    @staticmethod
    def get_visits_by_date_range(
        db: Session,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[DoctorVisit]:
        """Get visits within a specific date range"""
        return db.query(DoctorVisit)\
            .filter(
                DoctorVisit.owner_id == user_id,
                DoctorVisit.date >= start_date,
                DoctorVisit.date <= end_date
            )\
            .order_by(DoctorVisit.date.desc())\
            .all()

    @staticmethod
    def get_visits_by_doctor(
        db: Session,
        user_id: int,
        doctor_name: str
    ) -> List[DoctorVisit]:
        """Get all visits to a specific doctor"""
        return db.query(DoctorVisit)\
            .filter(
                DoctorVisit.owner_id == user_id,
                DoctorVisit.doctor_name.ilike(f"%{doctor_name}%")
            )\
            .order_by(DoctorVisit.date.desc())\
            .all() 