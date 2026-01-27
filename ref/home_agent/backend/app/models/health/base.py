from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from ...core.database import Base
from datetime import datetime

class WeightRecord(Base):
    __tablename__ = "weight_records"
    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="weight_records")

class HeightRecord(Base):
    __tablename__ = "height_records"
    id = Column(Integer, primary_key=True, index=True)
    height = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="height_records")

class BloodPressureRecord(Base):
    __tablename__ = "blood_pressure_records"
    id = Column(Integer, primary_key=True, index=True)
    systolic = Column(Integer)
    diastolic = Column(Integer)
    pulse = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="blood_pressure_records")

class HeartRateRecord(Base):
    __tablename__ = "heart_rate_records"
    id = Column(Integer, primary_key=True, index=True)
    heart_rate = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)
    activity_type = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="heart_rate_records")

class DoctorVisit(Base):
    __tablename__ = "doctor_visits"
    id = Column(Integer, primary_key=True, index=True)
    doctor_name = Column(String)
    specialty = Column(String)
    date = Column(DateTime)
    reason = Column(String)
    diagnosis = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="doctor_visits")

class ExerciseGoals(Base):
    __tablename__ = "exercise_goals"
    id = Column(Integer, primary_key=True, index=True)
    daily_steps = Column(Integer)
    weekly_exercise_minutes = Column(Integer)
    target_heart_rate = Column(Integer, nullable=True)
    preferred_activities = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="exercise_goals")

class DietaryGoals(Base):
    __tablename__ = "dietary_goals"
    id = Column(Integer, primary_key=True, index=True)
    daily_calories = Column(Integer)
    protein_grams = Column(Integer)
    carbs_grams = Column(Integer)
    fat_grams = Column(Integer)
    water_liters = Column(Float)
    restrictions = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="dietary_goals")

class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    dosage = Column(String)
    frequency = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    prescribing_doctor = Column(String)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="medications") 