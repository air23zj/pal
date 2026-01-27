from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ...core.database import Base

class ExerciseGoals(Base):
    __tablename__ = "exercise_goals"

    id = Column(Integer, primary_key=True, index=True)
    daily_steps = Column(Integer)
    weekly_exercise_minutes = Column(Integer)
    weekly_cardio_minutes = Column(Integer, nullable=True)
    weekly_strength_minutes = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Relationships
    owner = relationship("User", back_populates="exercise_goals") 