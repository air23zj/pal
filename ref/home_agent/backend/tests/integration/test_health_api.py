import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.health import HealthProfile, VitalSign, Medication

def test_create_health_profile(client: TestClient, test_auth_headers: dict):
    """Test creating a new health profile."""
    profile_data = {
        "height": 175.0,
        "weight": 70.0,
        "blood_type": "A+",
        "allergies": ["peanuts", "shellfish"],
        "medical_conditions": ["none"],
        "emergency_contact": {
            "name": "John Doe",
            "phone": "123-456-7890",
            "relationship": "spouse"
        }
    }
    response = client.post(
        "/api/v1/health/profile",
        json=profile_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["height"] == 175.0
    assert data["blood_type"] == "A+"
    assert "peanuts" in data["allergies"]

def test_get_health_profile(client: TestClient, test_auth_headers: dict):
    """Test retrieving health profile."""
    response = client.get(
        "/api/v1/health/profile",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "height" in data
    assert "weight" in data

def test_update_health_profile(client: TestClient, db: Session, test_auth_headers: dict):
    """Test updating health profile."""
    # Create test profile
    profile = HealthProfile(
        user_id=1,
        height=175.0,
        weight=70.0,
        blood_type="A+"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Update profile
    update_data = {
        "weight": 68.5,
        "medical_conditions": ["hypertension"]
    }
    response = client.put(
        "/api/v1/health/profile",
        json=update_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["weight"] == 68.5
    assert "hypertension" in data["medical_conditions"]

def test_record_vital_sign(client: TestClient, test_auth_headers: dict):
    """Test recording a vital sign."""
    vital_data = {
        "type": "blood_pressure",
        "value": "120/80",
        "notes": "Regular checkup"
    }
    response = client.post(
        "/api/v1/health/vitals",
        json=vital_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "blood_pressure"
    assert data["value"] == "120/80"

def test_get_vital_signs(client: TestClient, test_auth_headers: dict):
    """Test retrieving vital signs."""
    response = client.get(
        "/api/v1/health/vitals",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_add_medication(client: TestClient, test_auth_headers: dict):
    """Test adding a medication."""
    medication_data = {
        "name": "Aspirin",
        "dosage": "100mg",
        "frequency": "daily",
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "reminders_enabled": True
    }
    response = client.post(
        "/api/v1/health/medications",
        json=medication_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Aspirin"
    assert data["dosage"] == "100mg"

def test_get_medications(client: TestClient, test_auth_headers: dict):
    """Test retrieving medications."""
    response = client.get(
        "/api/v1/health/medications",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_medication(client: TestClient, db: Session, test_auth_headers: dict):
    """Test updating a medication."""
    # Create test medication
    medication = Medication(
        user_id=1,
        name="Aspirin",
        dosage="100mg",
        frequency="daily"
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)

    # Update medication
    update_data = {
        "dosage": "200mg",
        "reminders_enabled": False
    }
    response = client.put(
        f"/api/v1/health/medications/{medication.id}",
        json=update_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dosage"] == "200mg"
    assert data["reminders_enabled"] is False

def test_record_exercise(client: TestClient, test_auth_headers: dict):
    """Test recording exercise."""
    exercise_data = {
        "type": "running",
        "duration": 30,
        "distance": 5.0,
        "calories_burned": 300,
        "heart_rate_avg": 140
    }
    response = client.post(
        "/api/v1/health/exercise",
        json=exercise_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "running"
    assert data["duration"] == 30

def test_get_exercise_history(client: TestClient, test_auth_headers: dict):
    """Test retrieving exercise history."""
    response = client.get(
        "/api/v1/health/exercise",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_record_sleep(client: TestClient, test_auth_headers: dict):
    """Test recording sleep."""
    sleep_data = {
        "start_time": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
        "end_time": datetime.utcnow().isoformat(),
        "quality": "good",
        "interruptions": 1
    }
    response = client.post(
        "/api/v1/health/sleep",
        json=sleep_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["quality"] == "good"
    assert data["interruptions"] == 1

def test_get_sleep_records(client: TestClient, test_auth_headers: dict):
    """Test retrieving sleep records."""
    response = client.get(
        "/api/v1/health/sleep",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_log_meal(client: TestClient, test_auth_headers: dict):
    """Test logging a meal."""
    meal_data = {
        "meal_type": "lunch",
        "foods": [
            {"name": "chicken salad", "calories": 350},
            {"name": "apple", "calories": 95}
        ],
        "total_calories": 445
    }
    response = client.post(
        "/api/v1/health/meals",
        json=meal_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["meal_type"] == "lunch"
    assert data["total_calories"] == 445

def test_get_meal_logs(client: TestClient, test_auth_headers: dict):
    """Test retrieving meal logs."""
    response = client.get(
        "/api/v1/health/meals",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_set_health_goal(client: TestClient, test_auth_headers: dict):
    """Test setting a health goal."""
    goal_data = {
        "type": "weight",
        "target_value": 65.0,
        "current_value": 70.0,
        "deadline": (datetime.utcnow() + timedelta(days=90)).isoformat()
    }
    response = client.post(
        "/api/v1/health/goals",
        json=goal_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "weight"
    assert data["target_value"] == 65.0

def test_get_health_goals(client: TestClient, test_auth_headers: dict):
    """Test retrieving health goals."""
    response = client.get(
        "/api/v1/health/goals",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_health_metrics(client: TestClient, test_auth_headers: dict):
    """Test retrieving health metrics."""
    response = client.get(
        "/api/v1/health/metrics",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "bmi" in data
    assert "daily_calories" in data

def test_invalid_health_operations(client: TestClient, test_auth_headers: dict):
    """Test invalid health operations."""
    # Test creating profile with invalid data
    invalid_profile = {
        "height": -175.0,  # Negative height should be invalid
        "weight": -70.0    # Negative weight should be invalid
    }
    response = client.post(
        "/api/v1/health/profile",
        json=invalid_profile,
        headers=test_auth_headers
    )
    assert response.status_code == 422

    # Test recording vital sign with invalid data
    invalid_vital = {
        "type": "invalid_type",
        "value": "invalid"
    }
    response = client.post(
        "/api/v1/health/vitals",
        json=invalid_vital,
        headers=test_auth_headers
    )
    assert response.status_code == 422

    # Test setting goal with invalid data
    invalid_goal = {
        "type": "weight",
        "target_value": -65.0,  # Negative target should be invalid
        "deadline": "invalid_date"
    }
    response = client.post(
        "/api/v1/health/goals",
        json=invalid_goal,
        headers=test_auth_headers
    )
    assert response.status_code == 422 