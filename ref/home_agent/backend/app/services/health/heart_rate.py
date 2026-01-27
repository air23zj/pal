from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

from ...models.health.heart_rate import HeartRateRecord, ActivityLevel
from ...schemas.health.heart_rate import HeartRateRecordCreate, HeartRateRecordUpdate, HeartRateStats

class HeartRateService:
    @staticmethod
    def get_heart_rate_records(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[HeartRateRecord]:
        return db.query(HeartRateRecord)\
            .filter(HeartRateRecord.owner_id == user_id)\
            .order_by(HeartRateRecord.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_heart_rate_record(
        db: Session, user_id: int, record_id: int
    ) -> Optional[HeartRateRecord]:
        return db.query(HeartRateRecord)\
            .filter(HeartRateRecord.owner_id == user_id, HeartRateRecord.id == record_id)\
            .first()

    @staticmethod
    def create_heart_rate_record(
        db: Session, user_id: int, record: HeartRateRecordCreate
    ) -> HeartRateRecord:
        db_record = HeartRateRecord(**record.model_dump(), owner_id=user_id)
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def update_heart_rate_record(
        db: Session, user_id: int, record_id: int, record: HeartRateRecordUpdate
    ) -> Optional[HeartRateRecord]:
        db_record = HeartRateService.get_heart_rate_record(db, user_id, record_id)
        if db_record:
            update_data = record.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_record, field, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete_heart_rate_record(
        db: Session, user_id: int, record_id: int
    ) -> bool:
        db_record = HeartRateService.get_heart_rate_record(db, user_id, record_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def get_heart_rate_trend(
        db: Session, user_id: int, days: int = 30
    ) -> List[HeartRateRecord]:
        """Get heart rate records for trend analysis"""
        start_date = datetime.utcnow() - timedelta(days=days)
        return db.query(HeartRateRecord)\
            .filter(
                HeartRateRecord.owner_id == user_id,
                HeartRateRecord.date >= start_date
            )\
            .order_by(HeartRateRecord.date.asc())\
            .all()

    @staticmethod
    def get_heart_rate_stats(
        db: Session, user_id: int, days: int = 30
    ) -> HeartRateStats:
        """Get heart rate statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get basic stats
        basic_stats = db.query(
            func.avg(HeartRateRecord.heart_rate).label('avg'),
            func.max(HeartRateRecord.heart_rate).label('max'),
            func.min(HeartRateRecord.heart_rate).label('min')
        ).filter(
            HeartRateRecord.owner_id == user_id,
            HeartRateRecord.date >= start_date
        ).first()

        # Get resting heart rate average
        resting_avg = db.query(
            func.avg(HeartRateRecord.heart_rate).label('resting_avg')
        ).filter(
            HeartRateRecord.owner_id == user_id,
            HeartRateRecord.date >= start_date,
            HeartRateRecord.activity_level == ActivityLevel.RESTING
        ).scalar()

        # Get averages by activity level
        activity_averages = {}
        for level in ActivityLevel:
            avg = db.query(
                func.avg(HeartRateRecord.heart_rate)
            ).filter(
                HeartRateRecord.owner_id == user_id,
                HeartRateRecord.date >= start_date,
                HeartRateRecord.activity_level == level
            ).scalar()
            activity_averages[level] = round(avg, 1) if avg else None

        return HeartRateStats(
            average=round(basic_stats.avg, 1) if basic_stats.avg else 0,
            maximum=basic_stats.max if basic_stats.max else 0,
            minimum=basic_stats.min if basic_stats.min else 0,
            resting_average=round(resting_avg, 1) if resting_avg else None,
            by_activity_level=activity_averages
        ) 