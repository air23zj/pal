from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ...core.database import Base

class ActivityLevel(str, enum.Enum):
    RESTING = "resting"
    LIGHT = "light"
    MODERATE = "moderate"
    VIGOROUS = "vigorous"

class HeartRateRecord(Base):
    __tablename__ = "heart_rate_records"

    id = Column(Integer, primary_key=True, index=True)
    heart_rate = Column(Integer)  # Beats per minute
    activity_level = Column(Enum(ActivityLevel), nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="heart_rate_records") 