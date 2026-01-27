from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime

from ...core.database import Base

class BloodPressureRecord(Base):
    __tablename__ = "blood_pressure_records"

    id = Column(Integer, primary_key=True, index=True)
    systolic = Column(Integer)  # The top number
    diastolic = Column(Integer)  # The bottom number
    pulse = Column(Integer, nullable=True)  # Heart rate during measurement
    date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="blood_pressure_records") 