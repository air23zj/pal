from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ...models.health.weight import WeightRecord
from ...schemas.health.weight import WeightRecordCreate, WeightRecordUpdate

class WeightService:
    @staticmethod
    def get_weight_records(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[WeightRecord]:
        return db.query(WeightRecord).filter(WeightRecord.owner_id == user_id).order_by(WeightRecord.date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_weight_record(db: Session, user_id: int, record_id: int) -> Optional[WeightRecord]:
        return db.query(WeightRecord).filter(WeightRecord.owner_id == user_id, WeightRecord.id == record_id).first()

    @staticmethod
    def create_weight_record(db: Session, user_id: int, record: WeightRecordCreate) -> WeightRecord:
        db_record = WeightRecord(**record.model_dump(), owner_id=user_id)
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def update_weight_record(db: Session, user_id: int, record_id: int, record: WeightRecordUpdate) -> Optional[WeightRecord]:
        db_record = WeightService.get_weight_record(db, user_id, record_id)
        if db_record:
            update_data = record.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_record, field, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete_weight_record(db: Session, user_id: int, record_id: int) -> bool:
        db_record = WeightService.get_weight_record(db, user_id, record_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def get_weight_trend(db: Session, user_id: int, days: int = 30) -> List[WeightRecord]:
        """Get weight records for trend analysis"""
        start_date = datetime.utcnow() - timedelta(days=days)
        return db.query(WeightRecord).filter(
            WeightRecord.owner_id == user_id,
            WeightRecord.date >= start_date
        ).order_by(WeightRecord.date.asc()).all() 