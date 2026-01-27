import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.utilities import Reminder, Timer, Note

def test_create_reminder(client: TestClient, test_auth_headers: dict):
    """Test creating a new reminder."""
    reminder_data = {
        "title": "Test Reminder",
        "description": "Test Description",
        "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "priority": "high",
        "repeat_interval": "daily"
    }
    response = client.post(
        "/api/v1/utilities/reminders/",
        json=reminder_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Reminder"
    assert data["priority"] == "high"

def test_get_reminders(client: TestClient, test_auth_headers: dict):
    """Test retrieving user's reminders."""
    response = client.get(
        "/api/v1/utilities/reminders/",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_reminder(client: TestClient, db: Session, test_auth_headers: dict):
    """Test updating a reminder."""
    # Create test reminder
    reminder = Reminder(
        user_id=1,
        title="Original Title",
        description="Original Description",
        due_date=datetime.utcnow() + timedelta(days=1)
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    # Update reminder
    update_data = {
        "title": "Updated Title",
        "description": "Updated Description",
        "priority": "low"
    }
    response = client.put(
        f"/api/v1/utilities/reminders/{reminder.id}",
        json=update_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["priority"] == "low"

def test_create_timer(client: TestClient, test_auth_headers: dict):
    """Test creating a new timer."""
    timer_data = {
        "name": "Test Timer",
        "duration": 300  # 5 minutes
    }
    response = client.post(
        "/api/v1/utilities/timers/",
        json=timer_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Timer"
    assert data["duration"] == 300

def test_get_active_timers(client: TestClient, test_auth_headers: dict):
    """Test retrieving active timers."""
    response = client.get(
        "/api/v1/utilities/timers/active",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_stop_timer(client: TestClient, db: Session, test_auth_headers: dict):
    """Test stopping a timer."""
    # Create test timer
    timer = Timer(
        user_id=1,
        name="Test Timer",
        duration=300,
        start_time=datetime.utcnow(),
        status="running"
    )
    db.add(timer)
    db.commit()
    db.refresh(timer)

    response = client.post(
        f"/api/v1/utilities/timers/{timer.id}/stop",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"

def test_create_note(client: TestClient, test_auth_headers: dict):
    """Test creating a new note."""
    note_data = {
        "title": "Test Note",
        "content": "Test Content",
        "category": "personal",
        "is_pinned": True
    }
    response = client.post(
        "/api/v1/utilities/notes/",
        json=note_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["is_pinned"] is True

def test_get_notes(client: TestClient, test_auth_headers: dict):
    """Test retrieving user's notes."""
    response = client.get(
        "/api/v1/utilities/notes/",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_note(client: TestClient, db: Session, test_auth_headers: dict):
    """Test updating a note."""
    # Create test note
    note = Note(
        user_id=1,
        title="Original Title",
        content="Original Content"
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    # Update note
    update_data = {
        "title": "Updated Title",
        "content": "Updated Content",
        "is_pinned": True
    }
    response = client.put(
        f"/api/v1/utilities/notes/{note.id}",
        json=update_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Updated Content"

def test_calculator(client: TestClient, test_auth_headers: dict):
    """Test calculator functionality."""
    calc_data = {
        "expression": "2 + 2"
    }
    response = client.post(
        "/api/v1/utilities/calculator/calculate",
        json=calc_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["result"] == "4"

def test_get_calculator_history(client: TestClient, test_auth_headers: dict):
    """Test retrieving calculator history."""
    response = client.get(
        "/api/v1/utilities/calculator/history",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_unit_conversion(client: TestClient, test_auth_headers: dict):
    """Test unit conversion functionality."""
    conversion_data = {
        "from_unit": "km",
        "to_unit": "miles",
        "value": 10.0
    }
    response = client.post(
        "/api/v1/utilities/conversion/convert",
        json=conversion_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert abs(float(data["result"]) - 6.21371) < 0.0001

def test_get_conversion_history(client: TestClient, test_auth_headers: dict):
    """Test retrieving conversion history."""
    response = client.get(
        "/api/v1/utilities/conversion/history",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_utility_preferences(client: TestClient, test_auth_headers: dict):
    """Test retrieving utility preferences."""
    response = client.get(
        "/api/v1/utilities/preferences",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "default_reminder_advance" in data
    assert "preferred_unit_system" in data

def test_update_utility_preferences(client: TestClient, test_auth_headers: dict):
    """Test updating utility preferences."""
    preferences_data = {
        "default_reminder_advance": 15,
        "default_timer_duration": 600,
        "preferred_calculator_mode": "scientific",
        "preferred_unit_system": "imperial"
    }
    response = client.put(
        "/api/v1/utilities/preferences",
        json=preferences_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["default_reminder_advance"] == 15
    assert data["preferred_unit_system"] == "imperial"

def test_invalid_utility_operations(client: TestClient, test_auth_headers: dict):
    """Test invalid utility operations."""
    # Test creating reminder with invalid data
    invalid_reminder = {
        "title": "",  # Empty title should be invalid
        "due_date": "invalid_date"
    }
    response = client.post(
        "/api/v1/utilities/reminders/",
        json=invalid_reminder,
        headers=test_auth_headers
    )
    assert response.status_code == 422

    # Test calculator with invalid expression
    invalid_calc = {
        "expression": "2 +"  # Invalid expression
    }
    response = client.post(
        "/api/v1/utilities/calculator/calculate",
        json=invalid_calc,
        headers=test_auth_headers
    )
    assert response.status_code == 400

    # Test conversion with invalid units
    invalid_conversion = {
        "from_unit": "invalid",
        "to_unit": "invalid",
        "value": 10.0
    }
    response = client.post(
        "/api/v1/utilities/conversion/convert",
        json=invalid_conversion,
        headers=test_auth_headers
    )
    assert response.status_code == 400 