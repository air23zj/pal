import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.health import (
    HealthProfile,
    VitalSign,
    Medication,
    Exercise,
    Sleep,
    MealLog,
    HealthGoal,
    HealthMetric
)
from app.services.health import HealthService

def test_create_health_profile(db: Session, test_user: dict):
    """Test creating a health profile."""
    profile = HealthProfile(
        user_id=1,
        height=175.0,
        weight=70.0,
        blood_type="A+",
        allergies=["peanuts", "shellfish"],
        medical_conditions=["none"],
        emergency_contact={
            "name": "John Doe",
            "phone": "123-456-7890",
            "relationship": "spouse"
        }
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    assert profile.id is not None
    assert profile.height == 175.0
    assert profile.weight == 70.0
    assert "peanuts" in profile.allergies

def test_create_vital_sign(db: Session, test_user: dict):
    """Test creating a vital sign record."""
    vital = VitalSign(
        user_id=1,
        type="blood_pressure",
        value="120/80",
        timestamp=datetime.utcnow(),
        notes="Regular checkup"
    )
    db.add(vital)
    db.commit()
    db.refresh(vital)

    assert vital.id is not None
    assert vital.type == "blood_pressure"
    assert vital.value == "120/80"

def test_create_medication(db: Session, test_user: dict):
    """Test creating a medication record."""
    medication = Medication(
        user_id=1,
        name="Aspirin",
        dosage="100mg",
        frequency="daily",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        reminders_enabled=True
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)

    assert medication.id is not None
    assert medication.name == "Aspirin"
    assert medication.dosage == "100mg"
    assert medication.reminders_enabled is True

def test_create_exercise(db: Session, test_user: dict):
    """Test creating an exercise record."""
    exercise = Exercise(
        user_id=1,
        type="running",
        duration=30,
        distance=5.0,
        calories_burned=300,
        heart_rate_avg=140,
        timestamp=datetime.utcnow()
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)

    assert exercise.id is not None
    assert exercise.type == "running"
    assert exercise.duration == 30
    assert exercise.calories_burned == 300

def test_create_sleep(db: Session, test_user: dict):
    """Test creating a sleep record."""
    sleep = Sleep(
        user_id=1,
        start_time=datetime.utcnow() - timedelta(hours=8),
        end_time=datetime.utcnow(),
        quality="good",
        interruptions=1,
        notes="Restful sleep"
    )
    db.add(sleep)
    db.commit()
    db.refresh(sleep)

    assert sleep.id is not None
    assert sleep.quality == "good"
    assert sleep.interruptions == 1

def test_create_meal_log(db: Session, test_user: dict):
    """Test creating a meal log."""
    meal = MealLog(
        user_id=1,
        meal_type="lunch",
        foods=[
            {"name": "chicken salad", "calories": 350},
            {"name": "apple", "calories": 95}
        ],
        total_calories=445,
        timestamp=datetime.utcnow()
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)

    assert meal.id is not None
    assert meal.meal_type == "lunch"
    assert meal.total_calories == 445
    assert len(meal.foods) == 2

def test_create_health_goal(db: Session, test_user: dict):
    """Test creating a health goal."""
    goal = HealthGoal(
        user_id=1,
        type="weight",
        target_value=65.0,
        current_value=70.0,
        deadline=datetime.utcnow() + timedelta(days=90),
        status="in_progress"
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    assert goal.id is not None
    assert goal.type == "weight"
    assert goal.target_value == 65.0
    assert goal.status == "in_progress"

def test_create_health_metric(db: Session, test_user: dict):
    """Test creating a health metric."""
    metric = HealthMetric(
        user_id=1,
        type="bmi",
        value=22.5,
        timestamp=datetime.utcnow(),
        metadata={"category": "normal"}
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)

    assert metric.id is not None
    assert metric.type == "bmi"
    assert metric.value == 22.5

def test_health_service_profile(db: Session, test_user: dict):
    """Test the health service profile functionality."""
    service = HealthService(db)
    
    # Create profile
    profile = service.create_profile(
        user_id=1,
        height=175.0,
        weight=70.0,
        blood_type="A+"
    )
    assert profile.height == 175.0

    # Get profile
    retrieved_profile = service.get_profile(user_id=1)
    assert retrieved_profile.blood_type == "A+"

def test_health_service_vitals(db: Session, test_user: dict):
    """Test the health service vitals functionality."""
    service = HealthService(db)

    # Record vital sign
    vital = service.record_vital_sign(
        user_id=1,
        type="blood_pressure",
        value="120/80"
    )
    assert vital.type == "blood_pressure"

    # Get vital signs
    vitals = service.get_vital_signs(user_id=1)
    assert len(vitals) == 1

def test_health_service_medications(db: Session, test_user: dict):
    """Test the health service medications functionality."""
    service = HealthService(db)

    # Add medication
    medication = service.add_medication(
        user_id=1,
        name="Aspirin",
        dosage="100mg",
        frequency="daily"
    )
    assert medication.name == "Aspirin"

    # Get medications
    medications = service.get_medications(user_id=1)
    assert len(medications) == 1

def test_health_service_exercise(db: Session, test_user: dict):
    """Test the health service exercise functionality."""
    service = HealthService(db)

    # Record exercise
    exercise = service.record_exercise(
        user_id=1,
        type="running",
        duration=30,
        distance=5.0
    )
    assert exercise.type == "running"

    # Get exercise history
    history = service.get_exercise_history(user_id=1)
    assert len(history) == 1

def test_health_service_goals(db: Session, test_user: dict):
    """Test the health service goals functionality."""
    service = HealthService(db)

    # Set goal
    goal = service.set_goal(
        user_id=1,
        type="weight",
        target_value=65.0,
        deadline=datetime.utcnow() + timedelta(days=90)
    )
    assert goal.type == "weight"

    # Get goals
    goals = service.get_goals(user_id=1)
    assert len(goals) == 1

def test_health_service_metrics(db: Session, test_user: dict):
    """Test the health service metrics functionality."""
    service = HealthService(db)

    # Calculate BMI
    bmi = service.calculate_bmi(height=175.0, weight=70.0)
    assert 22.0 <= bmi <= 23.0

    # Get health metrics
    metrics = service.get_health_metrics(user_id=1)
    assert isinstance(metrics, dict) 