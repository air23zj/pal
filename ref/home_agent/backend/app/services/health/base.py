from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException

from ...models.health.base import (
    WeightRecord,
    HeightRecord,
    BloodPressureRecord,
    HeartRateRecord,
    DoctorVisit,
    ExerciseGoals,
    DietaryGoals,
    Medication
)
from ...schemas.health.base import (
    WeightRecordCreate,
    HeightRecordCreate,
    BloodPressureRecordCreate,
    HeartRateRecordCreate,
    DoctorVisitCreate,
    ExerciseGoalsCreate,
    DietaryGoalsCreate,
    MedicationCreate,
    HealthSummary
)

class HealthService:
    def __init__(self, db: Session):
        self.db = db

    # Weight Records
    def create_weight_record(self, user_id: int, record: WeightRecordCreate) -> WeightRecord:
        db_record = WeightRecord(**record.dict(), owner_id=user_id)
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    def get_weight_records(self, user_id: int, skip: int = 0, limit: int = 100) -> List[WeightRecord]:
        return self.db.query(WeightRecord).filter(
            WeightRecord.owner_id == user_id
        ).order_by(desc(WeightRecord.date)).offset(skip).limit(limit).all()

    def get_latest_weight(self, user_id: int) -> Optional[WeightRecord]:
        return self.db.query(WeightRecord).filter(
            WeightRecord.owner_id == user_id
        ).order_by(desc(WeightRecord.date)).first()

    # Height Records
    def create_height_record(self, user_id: int, record: HeightRecordCreate) -> HeightRecord:
        db_record = HeightRecord(**record.dict(), owner_id=user_id)
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    def get_height_records(self, user_id: int, skip: int = 0, limit: int = 100) -> List[HeightRecord]:
        return self.db.query(HeightRecord).filter(
            HeightRecord.owner_id == user_id
        ).order_by(desc(HeightRecord.date)).offset(skip).limit(limit).all()

    def get_latest_height(self, user_id: int) -> Optional[HeightRecord]:
        return self.db.query(HeightRecord).filter(
            HeightRecord.owner_id == user_id
        ).order_by(desc(HeightRecord.date)).first()

    # Blood Pressure Records
    def create_blood_pressure_record(self, user_id: int, record: BloodPressureRecordCreate) -> BloodPressureRecord:
        db_record = BloodPressureRecord(**record.dict(), owner_id=user_id)
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    def get_blood_pressure_records(self, user_id: int, skip: int = 0, limit: int = 100) -> List[BloodPressureRecord]:
        return self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.owner_id == user_id
        ).order_by(desc(BloodPressureRecord.date)).offset(skip).limit(limit).all()

    def get_latest_blood_pressure(self, user_id: int) -> Optional[BloodPressureRecord]:
        return self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.owner_id == user_id
        ).order_by(desc(BloodPressureRecord.date)).first()

    # Heart Rate Records
    def create_heart_rate_record(self, user_id: int, record: HeartRateRecordCreate) -> HeartRateRecord:
        db_record = HeartRateRecord(**record.dict(), owner_id=user_id)
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    def get_heart_rate_records(self, user_id: int, skip: int = 0, limit: int = 100) -> List[HeartRateRecord]:
        return self.db.query(HeartRateRecord).filter(
            HeartRateRecord.owner_id == user_id
        ).order_by(desc(HeartRateRecord.date)).offset(skip).limit(limit).all()

    def get_latest_heart_rate(self, user_id: int) -> Optional[HeartRateRecord]:
        return self.db.query(HeartRateRecord).filter(
            HeartRateRecord.owner_id == user_id
        ).order_by(desc(HeartRateRecord.date)).first()

    # Doctor Visits
    def create_doctor_visit(self, user_id: int, visit: DoctorVisitCreate) -> DoctorVisit:
        db_visit = DoctorVisit(**visit.dict(), owner_id=user_id)
        self.db.add(db_visit)
        self.db.commit()
        self.db.refresh(db_visit)
        return db_visit

    def get_doctor_visits(self, user_id: int, skip: int = 0, limit: int = 100) -> List[DoctorVisit]:
        return self.db.query(DoctorVisit).filter(
            DoctorVisit.owner_id == user_id
        ).order_by(desc(DoctorVisit.date)).offset(skip).limit(limit).all()

    def get_upcoming_doctor_visits(self, user_id: int) -> List[DoctorVisit]:
        now = datetime.utcnow()
        return self.db.query(DoctorVisit).filter(
            DoctorVisit.owner_id == user_id,
            DoctorVisit.date >= now
        ).order_by(DoctorVisit.date).all()

    # Exercise Goals
    def create_or_update_exercise_goals(self, user_id: int, goals: ExerciseGoalsCreate) -> ExerciseGoals:
        db_goals = self.db.query(ExerciseGoals).filter(
            ExerciseGoals.owner_id == user_id
        ).first()

        if db_goals:
            for key, value in goals.dict().items():
                setattr(db_goals, key, value)
        else:
            db_goals = ExerciseGoals(**goals.dict(), owner_id=user_id)
            self.db.add(db_goals)

        self.db.commit()
        self.db.refresh(db_goals)
        return db_goals

    def get_exercise_goals(self, user_id: int) -> Optional[ExerciseGoals]:
        return self.db.query(ExerciseGoals).filter(
            ExerciseGoals.owner_id == user_id
        ).first()

    # Dietary Goals
    def create_or_update_dietary_goals(self, user_id: int, goals: DietaryGoalsCreate) -> DietaryGoals:
        db_goals = self.db.query(DietaryGoals).filter(
            DietaryGoals.owner_id == user_id
        ).first()

        if db_goals:
            for key, value in goals.dict().items():
                setattr(db_goals, key, value)
        else:
            db_goals = DietaryGoals(**goals.dict(), owner_id=user_id)
            self.db.add(db_goals)

        self.db.commit()
        self.db.refresh(db_goals)
        return db_goals

    def get_dietary_goals(self, user_id: int) -> Optional[DietaryGoals]:
        return self.db.query(DietaryGoals).filter(
            DietaryGoals.owner_id == user_id
        ).first()

    # Medications
    def create_medication(self, user_id: int, medication: MedicationCreate) -> Medication:
        db_medication = Medication(**medication.dict(), owner_id=user_id)
        self.db.add(db_medication)
        self.db.commit()
        self.db.refresh(db_medication)
        return db_medication

    def get_medications(self, user_id: int, active_only: bool = False) -> List[Medication]:
        query = self.db.query(Medication).filter(Medication.owner_id == user_id)
        if active_only:
            query = query.filter(Medication.is_active == True)
        return query.order_by(Medication.name).all()

    def update_medication(self, medication_id: int, user_id: int, is_active: bool) -> Medication:
        medication = self.db.query(Medication).filter(
            Medication.id == medication_id,
            Medication.owner_id == user_id
        ).first()
        
        if not medication:
            raise HTTPException(status_code=404, detail="Medication not found")
        
        medication.is_active = is_active
        self.db.commit()
        self.db.refresh(medication)
        return medication

    # Health Summary
    def get_health_summary(self, user_id: int) -> HealthSummary:
        return HealthSummary(
            latest_weight=self.get_latest_weight(user_id),
            latest_height=self.get_latest_height(user_id),
            latest_blood_pressure=self.get_latest_blood_pressure(user_id),
            latest_heart_rate=self.get_latest_heart_rate(user_id),
            upcoming_doctor_visits=self.get_upcoming_doctor_visits(user_id),
            exercise_goals=self.get_exercise_goals(user_id),
            dietary_goals=self.get_dietary_goals(user_id),
            active_medications=self.get_medications(user_id, active_only=True)
        ) 