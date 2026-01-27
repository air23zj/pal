from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ...core.database import Base

class DietType(str, enum.Enum):
    STANDARD = "standard"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    KETO = "keto"
    PALEO = "paleo"
    MEDITERRANEAN = "mediterranean"
    LOW_CARB = "low_carb"
    LOW_FAT = "low_fat"
    GLUTEN_FREE = "gluten_free"
    CUSTOM = "custom"

class DietaryGoals(Base):
    __tablename__ = "dietary_goals"

    id = Column(Integer, primary_key=True, index=True)
    diet_type = Column(Enum(DietType), default=DietType.STANDARD)
    daily_calories = Column(Integer)  # Target daily calorie intake
    protein_grams = Column(Integer, nullable=True)  # Target daily protein in grams
    carbs_grams = Column(Integer, nullable=True)  # Target daily carbs in grams
    fat_grams = Column(Integer, nullable=True)  # Target daily fat in grams
    fiber_grams = Column(Integer, nullable=True)  # Target daily fiber in grams
    water_ml = Column(Integer)  # Target daily water intake in milliliters
    meals_per_day = Column(Integer, default=3)
    snacks_per_day = Column(Integer, default=2)
    excluded_foods = Column(JSON, nullable=True)  # List of foods to avoid
    preferred_foods = Column(JSON, nullable=True)  # List of preferred foods
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)  # Optional end date for the goal
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="dietary_goals") 