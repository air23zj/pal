from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

from ...models.health.exercise_goals import ExerciseGoals
from ...schemas.health.exercise_goals import ExerciseGoalsCreate, ExerciseGoalsUpdate

class ExerciseGoalsService:
    @staticmethod
    def get_exercise_goals(
        db: Session, user_id: int
    ) -> Optional[ExerciseGoals]:
        """Get current active exercise goals for user"""
        return db.query(ExerciseGoals)\
            .filter(
                ExerciseGoals.owner_id == user_id,
                ExerciseGoals.is_active == True
            )\
            .first()

    @staticmethod
    def get_exercise_goals_history(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[ExerciseGoals]:
        """Get history of exercise goals"""
        return db.query(ExerciseGoals)\
            .filter(ExerciseGoals.owner_id == user_id)\
            .order_by(ExerciseGoals.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def create_exercise_goals(
        db: Session, user_id: int, goals: ExerciseGoalsCreate
    ) -> ExerciseGoals:
        # Deactivate current active goals if they exist
        current_goals = ExerciseGoalsService.get_exercise_goals(db, user_id)
        if current_goals:
            current_goals.is_active = False
            db.commit()

        # Create new goals
        db_goals = ExerciseGoals(**goals.model_dump(), owner_id=user_id)
        db.add(db_goals)
        db.commit()
        db.refresh(db_goals)
        return db_goals

    @staticmethod
    def update_exercise_goals(
        db: Session, user_id: int, goals: ExerciseGoalsUpdate
    ) -> Optional[ExerciseGoals]:
        db_goals = ExerciseGoalsService.get_exercise_goals(db, user_id)
        if db_goals:
            update_data = goals.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_goals, field, value)
            db.commit()
            db.refresh(db_goals)
        return db_goals

    @staticmethod
    def deactivate_exercise_goals(
        db: Session, user_id: int
    ) -> bool:
        db_goals = ExerciseGoalsService.get_exercise_goals(db, user_id)
        if db_goals:
            db_goals.is_active = False
            db.commit()
            return True
        return False

    @staticmethod
    def get_exercise_progress(
        db: Session, user_id: int, days: int = 7
    ) -> Dict:
        """Get progress towards exercise goals"""
        goals = ExerciseGoalsService.get_exercise_goals(db, user_id)
        if not goals:
            return {
                "has_goals": False,
                "message": "No active exercise goals found"
            }

        # Calculate weekly targets
        weekly_targets = {
            "steps": goals.daily_steps * 7,
            "total_exercise": goals.weekly_exercise_minutes,
            "cardio": goals.weekly_cardio_minutes,
            "strength": goals.weekly_strength_minutes
        }

        # Here you would typically integrate with a fitness tracking API
        # or your own activity tracking system to get actual progress
        # For now, we'll return the targets
        return {
            "has_goals": True,
            "targets": weekly_targets,
            "progress": {
                "steps": 0,  # To be integrated with activity tracking
                "total_exercise": 0,
                "cardio": 0,
                "strength": 0
            },
            "completion_percentage": {
                "steps": 0,
                "total_exercise": 0,
                "cardio": 0,
                "strength": 0
            }
        } 