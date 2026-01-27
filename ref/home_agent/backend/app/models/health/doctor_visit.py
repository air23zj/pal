from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ...core.database import Base

class VisitType(str, enum.Enum):
    ROUTINE_CHECKUP = "routine_checkup"
    FOLLOW_UP = "follow_up"
    SPECIALIST = "specialist"
    EMERGENCY = "emergency"
    VACCINATION = "vaccination"
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"

class DoctorVisit(Base):
    __tablename__ = "doctor_visits"

    id = Column(Integer, primary_key=True, index=True)
    doctor_name = Column(String)
    specialty = Column(String, nullable=True)
    visit_type = Column(Enum(VisitType))
    date = Column(DateTime)
    duration_minutes = Column(Integer, nullable=True)
    reason = Column(String)
    diagnosis = Column(String, nullable=True)
    prescription = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    follow_up_needed = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="doctor_visits") 