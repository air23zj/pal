from pydantic import BaseModel, Field, validator, conlist
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

class DietType(str, Enum):
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

class MacroNutrients(BaseModel):
    protein_percentage: float = Field(..., ge=0, le=100)
    carbs_percentage: float = Field(..., ge=0, le=100)
    fat_percentage: float = Field(..., ge=0, le=100)

    @validator('fat_percentage')
    def validate_macros_total(cls, v, values):
        if 'protein_percentage' in values and 'carbs_percentage' in values:
            total = values['protein_percentage'] + values['carbs_percentage'] + v
            if not 99.0 <= total <= 100.0:
                raise ValueError("Macronutrient percentages must sum to 100%")
        return v

class DietaryGoalsBase(BaseModel):
    diet_type: DietType = Field(default=DietType.STANDARD)
    daily_calories: int = Field(..., ge=800, le=10000)
    protein_grams: Optional[int] = Field(None, ge=0, le=500)
    carbs_grams: Optional[int] = Field(None, ge=0, le=1000)
    fat_grams: Optional[int] = Field(None, ge=0, le=500)
    fiber_grams: Optional[int] = Field(None, ge=0, le=100)
    water_ml: int = Field(..., ge=500, le=10000)
    meals_per_day: int = Field(default=3, ge=1, le=10)
    snacks_per_day: int = Field(default=2, ge=0, le=10)
    excluded_foods: Optional[List[str]] = Field(default=None, max_items=100)
    preferred_foods: Optional[List[str]] = Field(default=None, max_items=100)
    notes: Optional[str] = None
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v

    @validator('protein_grams', 'carbs_grams', 'fat_grams')
    def validate_macros(cls, v, values):
        if v is not None and 'daily_calories' in values:
            total_calories = 0
            if 'protein_grams' in values and values['protein_grams']:
                total_calories += values['protein_grams'] * 4
            if 'carbs_grams' in values and values['carbs_grams']:
                total_calories += values['carbs_grams'] * 4
            if 'fat_grams' in values and values['fat_grams']:
                total_calories += values['fat_grams'] * 9
            
            if total_calories > values['daily_calories']:
                raise ValueError("Total calories from macronutrients exceeds daily calorie goal")
        return v

class DietaryGoalsCreate(DietaryGoalsBase):
    pass

class DietaryGoalsUpdate(BaseModel):
    diet_type: Optional[DietType] = None
    daily_calories: Optional[int] = Field(None, ge=800, le=10000)
    protein_grams: Optional[int] = Field(None, ge=0, le=500)
    carbs_grams: Optional[int] = Field(None, ge=0, le=1000)
    fat_grams: Optional[int] = Field(None, ge=0, le=500)
    fiber_grams: Optional[int] = Field(None, ge=0, le=100)
    water_ml: Optional[int] = Field(None, ge=500, le=10000)
    meals_per_day: Optional[int] = Field(None, ge=1, le=10)
    snacks_per_day: Optional[int] = Field(None, ge=0, le=10)
    excluded_foods: Optional[List[str]] = Field(None, max_items=100)
    preferred_foods: Optional[List[str]] = Field(None, max_items=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None

class DietaryGoalsInDBBase(DietaryGoalsBase):
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DietaryGoals(DietaryGoalsInDBBase):
    pass

class DietaryGoalsStats(BaseModel):
    active_goals: Optional[DietaryGoals]
    total_goals_count: int
    goals_history: List[DietaryGoals]
    average_daily_calories: float
    macro_distribution: Optional[MacroNutrients]
    diet_type_history: Dict[DietType, int]  # Count of each diet type used 