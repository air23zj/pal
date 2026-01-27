from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

from ...models.health.blood_pressure import BloodPressureRecord
from ...schemas.health.blood_pressure import BloodPressureRecordCreate, BloodPressureRecordUpdate

class BloodPressureService:
    @staticmethod
    def get_blood_pressure_records(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[BloodPressureRecord]:
        return db.query(BloodPressureRecord)\
            .filter(BloodPressureRecord.owner_id == user_id)\
            .order_by(BloodPressureRecord.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_blood_pressure_record(
        db: Session, user_id: int, record_id: int
    ) -> Optional[BloodPressureRecord]:
        return db.query(BloodPressureRecord)\
            .filter(BloodPressureRecord.owner_id == user_id, BloodPressureRecord.id == record_id)\
            .first()

    @staticmethod
    def create_blood_pressure_record(
        db: Session, user_id: int, record: BloodPressureRecordCreate
    ) -> BloodPressureRecord:
        db_record = BloodPressureRecord(**record.model_dump(), owner_id=user_id)
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def update_blood_pressure_record(
        db: Session, user_id: int, record_id: int, record: BloodPressureRecordUpdate
    ) -> Optional[BloodPressureRecord]:
        db_record = BloodPressureService.get_blood_pressure_record(db, user_id, record_id)
        if db_record:
            update_data = record.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_record, field, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete_blood_pressure_record(
        db: Session, user_id: int, record_id: int
    ) -> bool:
        db_record = BloodPressureService.get_blood_pressure_record(db, user_id, record_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def get_blood_pressure_trend(
        db: Session, user_id: int, days: int = 30
    ) -> List[BloodPressureRecord]:
        """Get blood pressure records for trend analysis"""
        start_date = datetime.utcnow() - timedelta(days=days)
        return db.query(BloodPressureRecord)\
            .filter(
                BloodPressureRecord.owner_id == user_id,
                BloodPressureRecord.date >= start_date
            )\
            .order_by(BloodPressureRecord.date.asc())\
            .all()

    @staticmethod
    def get_blood_pressure_stats(
        db: Session, user_id: int, days: int = 30
    ) -> Dict:
        """Get blood pressure statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        result = db.query(
            func.avg(BloodPressureRecord.systolic).label('avg_systolic'),
            func.avg(BloodPressureRecord.diastolic).label('avg_diastolic'),
            func.avg(BloodPressureRecord.pulse).label('avg_pulse'),
            func.max(BloodPressureRecord.systolic).label('max_systolic'),
            func.max(BloodPressureRecord.diastolic).label('max_diastolic'),
            func.min(BloodPressureRecord.systolic).label('min_systolic'),
            func.min(BloodPressureRecord.diastolic).label('min_diastolic')
        ).filter(
            BloodPressureRecord.owner_id == user_id,
            BloodPressureRecord.date >= start_date
        ).first()

        return {
            'average': {
                'systolic': round(result.avg_systolic, 1) if result.avg_systolic else None,
                'diastolic': round(result.avg_diastolic, 1) if result.avg_diastolic else None,
                'pulse': round(result.avg_pulse, 1) if result.avg_pulse else None
            },
            'maximum': {
                'systolic': result.max_systolic,
                'diastolic': result.max_diastolic
            },
            'minimum': {
                'systolic': result.min_systolic,
                'diastolic': result.min_diastolic
            }
        } 