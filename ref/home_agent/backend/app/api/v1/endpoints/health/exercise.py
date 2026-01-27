from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .....core.database import get_db
from .....services.health.exercise_goals import ExerciseGoalsService
from .....schemas.health.exercise_goals import (
    ExerciseGoals,
    ExerciseGoalsCreate,
    ExerciseGoalsUpdate
)
from ....dependencies.auth import get_current_user
from .....schemas.user import User

router = APIRouter()

@router.get("/goals", response_model=ExerciseGoals)
def get_exercise_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current active exercise goals.
    """
    goals = ExerciseGoalsService.get_exercise_goals(db, current_user.id)
    if not goals:
        raise HTTPException(status_code=404, detail="No active exercise goals found")
    return goals

@router.get("/goals/history", response_model=List[ExerciseGoals])
def get_exercise_goals_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get history of exercise goals.
    """
    goals = ExerciseGoalsService.get_exercise_goals_history(db, current_user.id, skip, limit)
    return goals

@router.post("/goals", response_model=ExerciseGoals)
def create_exercise_goals(
    *,
    goals_in: ExerciseGoalsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new exercise goals (deactivates current goals if they exist).
    """
    goals = ExerciseGoalsService.create_exercise_goals(db, current_user.id, goals_in)
    return goals

@router.put("/goals", response_model=ExerciseGoals)
def update_exercise_goals(
    *,
    goals_in: ExerciseGoalsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current active exercise goals.
    """
    goals = ExerciseGoalsService.update_exercise_goals(db, current_user.id, goals_in)
    if not goals:
        raise HTTPException(status_code=404, detail="No active exercise goals found")
    return goals

@router.post("/goals/deactivate")
def deactivate_exercise_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Deactivate current exercise goals.
    """
    success = ExerciseGoalsService.deactivate_exercise_goals(db, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="No active exercise goals found")
    return {"message": "Exercise goals deactivated successfully"}

@router.get("/progress/{days}", response_model=Dict)
def get_exercise_progress(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get progress towards exercise goals over specified number of days.
    """
    progress = ExerciseGoalsService.get_exercise_progress(db, current_user.id, days)
    return progress 