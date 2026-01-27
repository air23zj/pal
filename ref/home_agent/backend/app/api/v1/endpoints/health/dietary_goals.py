from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .....core.database import get_db
from .....services.health.dietary_goals import DietaryGoalsService
from .....schemas.health.dietary_goals import (
    DietaryGoals,
    DietaryGoalsCreate,
    DietaryGoalsUpdate,
    DietaryGoalsStats,
    DietType
)
from ....dependencies.auth import get_current_user
from .....schemas.user import User

router = APIRouter()

@router.get("/", response_model=List[DietaryGoals])
def get_dietary_goals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve dietary goals history for the current user.
    """
    goals = DietaryGoalsService.get_dietary_goals(db, current_user.id, skip, limit)
    return goals

@router.get("/active", response_model=DietaryGoals)
def get_active_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current active dietary goals.
    """
    goals = DietaryGoalsService.get_active_goals(db, current_user.id)
    if not goals:
        raise HTTPException(status_code=404, detail="No active dietary goals found")
    return goals

@router.post("/", response_model=DietaryGoals)
def create_dietary_goals(
    *,
    goals_in: DietaryGoalsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create new dietary goals (deactivates current goals if they exist).
    """
    goals = DietaryGoalsService.create_dietary_goals(db, current_user.id, goals_in)
    return goals

@router.get("/{goal_id}", response_model=DietaryGoals)
def get_dietary_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific dietary goals by ID.
    """
    goals = DietaryGoalsService.get_dietary_goal(db, current_user.id, goal_id)
    if not goals:
        raise HTTPException(status_code=404, detail="Dietary goals not found")
    return goals

@router.put("/{goal_id}", response_model=DietaryGoals)
def update_dietary_goals(
    *,
    goal_id: int,
    goals_in: DietaryGoalsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update dietary goals.
    """
    goals = DietaryGoalsService.update_dietary_goals(
        db, current_user.id, goal_id, goals_in
    )
    if not goals:
        raise HTTPException(status_code=404, detail="Dietary goals not found")
    return goals

@router.delete("/{goal_id}")
def delete_dietary_goals(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete dietary goals.
    """
    success = DietaryGoalsService.delete_dietary_goals(db, current_user.id, goal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dietary goals not found")
    return {"message": "Dietary goals successfully deleted"}

@router.get("/stats/summary", response_model=DietaryGoalsStats)
def get_dietary_goals_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get comprehensive statistics about dietary goals.
    Includes active goals, history, averages, and macro distributions.
    """
    stats = DietaryGoalsService.get_dietary_goals_stats(db, current_user.id)
    return stats 