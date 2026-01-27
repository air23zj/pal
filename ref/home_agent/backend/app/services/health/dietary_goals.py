from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func, desc

from ...models.health.dietary_goals import DietaryGoals, DietType
from ...schemas.health.dietary_goals import (
    DietaryGoalsCreate,
    DietaryGoalsUpdate,
    DietaryGoalsStats,
    MacroNutrients
)

class DietaryGoalsService:
    @staticmethod
    def get_dietary_goals(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[DietaryGoals]:
        return db.query(DietaryGoals)\
            .filter(DietaryGoals.owner_id == user_id)\
            .order_by(DietaryGoals.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_active_goals(
        db: Session, user_id: int
    ) -> Optional[DietaryGoals]:
        return db.query(DietaryGoals)\
            .filter(
                DietaryGoals.owner_id == user_id,
                DietaryGoals.is_active == True
            )\
            .first()

    @staticmethod
    def get_dietary_goal(
        db: Session, user_id: int, goal_id: int
    ) -> Optional[DietaryGoals]:
        return db.query(DietaryGoals)\
            .filter(
                DietaryGoals.owner_id == user_id,
                DietaryGoals.id == goal_id
            )\
            .first()

    @staticmethod
    def create_dietary_goals(
        db: Session, user_id: int, goals: DietaryGoalsCreate
    ) -> DietaryGoals:
        # Deactivate current active goals if they exist
        current_goals = DietaryGoalsService.get_active_goals(db, user_id)
        if current_goals:
            current_goals.is_active = False
            current_goals.end_date = datetime.utcnow()
            db.commit()

        # Create new goals
        db_goals = DietaryGoals(**goals.model_dump(), owner_id=user_id)
        db.add(db_goals)
        db.commit()
        db.refresh(db_goals)
        return db_goals

    @staticmethod
    def update_dietary_goals(
        db: Session, user_id: int, goal_id: int, goals: DietaryGoalsUpdate
    ) -> Optional[DietaryGoals]:
        db_goals = DietaryGoalsService.get_dietary_goal(db, user_id, goal_id)
        if db_goals:
            update_data = goals.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_goals, field, value)
            db.commit()
            db.refresh(db_goals)
        return db_goals

    @staticmethod
    def delete_dietary_goals(
        db: Session, user_id: int, goal_id: int
    ) -> bool:
        db_goals = DietaryGoalsService.get_dietary_goal(db, user_id, goal_id)
        if db_goals:
            db.delete(db_goals)
            db.commit()
            return True
        return False

    @staticmethod
    def calculate_macro_distribution(goals: DietaryGoals) -> Optional[MacroNutrients]:
        """Calculate macronutrient distribution from grams"""
        if not all([goals.protein_grams, goals.carbs_grams, goals.fat_grams]):
            return None

        total_calories = (
            goals.protein_grams * 4 +
            goals.carbs_grams * 4 +
            goals.fat_grams * 9
        )

        if total_calories == 0:
            return None

        return MacroNutrients(
            protein_percentage=round(goals.protein_grams * 4 / total_calories * 100, 1),
            carbs_percentage=round(goals.carbs_grams * 4 / total_calories * 100, 1),
            fat_percentage=round(goals.fat_grams * 9 / total_calories * 100, 1)
        )

    @staticmethod
    def get_dietary_goals_stats(
        db: Session, user_id: int
    ) -> DietaryGoalsStats:
        """Get comprehensive statistics about dietary goals"""
        # Get active goals
        active_goals = DietaryGoalsService.get_active_goals(db, user_id)

        # Get total count
        total_count = db.query(func.count(DietaryGoals.id))\
            .filter(DietaryGoals.owner_id == user_id)\
            .scalar()

        # Get goals history
        goals_history = db.query(DietaryGoals)\
            .filter(DietaryGoals.owner_id == user_id)\
            .order_by(DietaryGoals.created_at.desc())\
            .limit(5)\
            .all()

        # Calculate average daily calories
        avg_calories = db.query(func.avg(DietaryGoals.daily_calories))\
            .filter(DietaryGoals.owner_id == user_id)\
            .scalar()

        # Get diet type history
        diet_type_counts = {}
        for diet_type in DietType:
            count = db.query(func.count(DietaryGoals.id))\
                .filter(
                    DietaryGoals.owner_id == user_id,
                    DietaryGoals.diet_type == diet_type
                )\
                .scalar()
            diet_type_counts[diet_type] = count

        # Calculate macro distribution for active goals
        macro_distribution = None
        if active_goals:
            macro_distribution = DietaryGoalsService.calculate_macro_distribution(active_goals)

        return DietaryGoalsStats(
            active_goals=active_goals,
            total_goals_count=total_count,
            goals_history=goals_history,
            average_daily_calories=round(avg_calories, 1) if avg_calories else 0,
            macro_distribution=macro_distribution,
            diet_type_history=diet_type_counts
        ) 