from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ExerciseGoalsBase(BaseModel):
    daily_steps: int = Field(..., ge=0, le=100000)
    weekly_exercise_minutes: int = Field(..., ge=0, le=10080)  # Max minutes in a week
    weekly_cardio_minutes: Optional[int] = Field(None, ge=0, le=10080)
    weekly_strength_minutes: Optional[int] = Field(None, ge=0, le=10080)
    notes: Optional[str] = None

class ExerciseGoalsCreate(ExerciseGoalsBase):
    pass

class ExerciseGoalsUpdate(BaseModel):
    daily_steps: Optional[int] = Field(None, ge=0, le=100000)
    weekly_exercise_minutes: Optional[int] = Field(None, ge=0, le=10080)
    weekly_cardio_minutes: Optional[int] = Field(None, ge=0, le=10080)
    weekly_strength_minutes: Optional[int] = Field(None, ge=0, le=10080)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class ExerciseGoalsInDBBase(ExerciseGoalsBase):
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExerciseGoals(ExerciseGoalsInDBBase):
    pass 