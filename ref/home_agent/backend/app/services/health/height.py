from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

from ...models.health.height import HeightRecord, MeasurementUnit
from ...schemas.health.height import HeightRecordCreate, HeightRecordUpdate, HeightStats

class HeightService:
    @staticmethod
    def get_height_records(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[HeightRecord]:
        return db.query(HeightRecord)\
            .filter(HeightRecord.owner_id == user_id)\
            .order_by(HeightRecord.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_height_record(
        db: Session, user_id: int, record_id: int
    ) -> Optional[HeightRecord]:
        return db.query(HeightRecord)\
            .filter(HeightRecord.owner_id == user_id, HeightRecord.id == record_id)\
            .first()

    @staticmethod
    def create_height_record(
        db: Session, user_id: int, record: HeightRecordCreate
    ) -> HeightRecord:
        db_record = HeightRecord(**record.model_dump(), owner_id=user_id)
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def update_height_record(
        db: Session, user_id: int, record_id: int, record: HeightRecordUpdate
    ) -> Optional[HeightRecord]:
        db_record = HeightService.get_height_record(db, user_id, record_id)
        if db_record:
            update_data = record.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_record, field, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete_height_record(
        db: Session, user_id: int, record_id: int
    ) -> bool:
        db_record = HeightService.get_height_record(db, user_id, record_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def convert_height(height: float, from_unit: MeasurementUnit, to_unit: MeasurementUnit) -> float:
        """Convert height between units"""
        if from_unit == to_unit:
            return height
        if from_unit == MeasurementUnit.CM and to_unit == MeasurementUnit.INCHES:
            return height / 2.54
        if from_unit == MeasurementUnit.INCHES and to_unit == MeasurementUnit.CM:
            return height * 2.54
        raise ValueError("Invalid unit conversion")

    @staticmethod
    def get_height_stats(
        db: Session, user_id: int
    ) -> HeightStats:
        """Get height statistics and growth analysis"""
        # Get latest record
        latest_record = db.query(HeightRecord)\
            .filter(HeightRecord.owner_id == user_id)\
            .order_by(HeightRecord.date.desc())\
            .first()

        if not latest_record:
            raise ValueError("No height records found")

        # Get total number of records
        record_count = db.query(func.count(HeightRecord.id))\
            .filter(HeightRecord.owner_id == user_id)\
            .scalar()

        # Calculate growth rate if multiple records exist
        growth_rate = None
        if record_count > 1:
            # Get oldest record
            oldest_record = db.query(HeightRecord)\
                .filter(HeightRecord.owner_id == user_id)\
                .order_by(HeightRecord.date.asc())\
                .first()

            # Convert heights to same unit if necessary
            latest_height = latest_record.height
            oldest_height = oldest_record.height

            if latest_record.unit != oldest_record.unit:
                oldest_height = HeightService.convert_height(
                    oldest_height,
                    oldest_record.unit,
                    latest_record.unit
                )

            # Calculate years between measurements
            years = (latest_record.date - oldest_record.date).days / 365.25

            if years > 0:
                growth_rate = (latest_height - oldest_height) / years

        return HeightStats(
            latest_height=latest_record.height,
            latest_unit=latest_record.unit,
            latest_date=latest_record.date,
            history_count=record_count,
            growth_rate=round(growth_rate, 2) if growth_rate is not None else None
        ) 