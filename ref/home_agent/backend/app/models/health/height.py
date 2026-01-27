from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ...core.database import Base

class MeasurementUnit(str, enum.Enum):
    CM = "cm"
    INCHES = "inches"

class HeightRecord(Base):
    __tablename__ = "height_records"

    id = Column(Integer, primary_key=True, index=True)
    height = Column(Float)  # Height in the specified unit
    unit = Column(Enum(MeasurementUnit), default=MeasurementUnit.CM)
    date = Column(DateTime, default=datetime.utcnow)
    measured_by = Column(String, nullable=True)  # e.g., "Self", "Doctor", "Nurse"
    notes = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="height_records") 