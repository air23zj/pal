import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.utilities import (
    Reminder,
    Timer,
    Note,
    Calculator,
    Conversion,
    UtilityPreference
)
from app.services.utilities import UtilitiesService

def test_create_reminder(db: Session, test_user: dict):
    """Test creating a reminder."""
    reminder = Reminder(
        user_id=1,
        title="Test Reminder",
        description="Test Description",
        due_date=datetime.utcnow() + timedelta(days=1),
        priority="high",
        status="pending",
        repeat_interval="daily"
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    assert reminder.id is not None
    assert reminder.title == "Test Reminder"
    assert reminder.priority == "high"
    assert reminder.status == "pending"

def test_create_timer(db: Session, test_user: dict):
    """Test creating a timer."""
    timer = Timer(
        user_id=1,
        name="Test Timer",
        duration=300,  # 5 minutes
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(minutes=5),
        status="running"
    )
    db.add(timer)
    db.commit()
    db.refresh(timer)

    assert timer.id is not None
    assert timer.name == "Test Timer"
    assert timer.duration == 300
    assert timer.status == "running"

def test_create_note(db: Session, test_user: dict):
    """Test creating a note."""
    note = Note(
        user_id=1,
        title="Test Note",
        content="Test Content",
        category="personal",
        is_pinned=True,
        metadata={"tags": ["important", "todo"]}
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    assert note.id is not None
    assert note.title == "Test Note"
    assert note.content == "Test Content"
    assert note.is_pinned is True

def test_create_calculator_history(db: Session, test_user: dict):
    """Test creating a calculator history entry."""
    calc = Calculator(
        user_id=1,
        expression="2 + 2",
        result="4",
        timestamp=datetime.utcnow()
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)

    assert calc.id is not None
    assert calc.expression == "2 + 2"
    assert calc.result == "4"

def test_create_conversion(db: Session, test_user: dict):
    """Test creating a conversion record."""
    conversion = Conversion(
        user_id=1,
        from_unit="km",
        to_unit="miles",
        from_value=10.0,
        to_value=6.21371,
        category="distance",
        timestamp=datetime.utcnow()
    )
    db.add(conversion)
    db.commit()
    db.refresh(conversion)

    assert conversion.id is not None
    assert conversion.from_unit == "km"
    assert conversion.to_unit == "miles"
    assert conversion.category == "distance"

def test_create_utility_preference(db: Session, test_user: dict):
    """Test creating utility preferences."""
    preference = UtilityPreference(
        user_id=1,
        default_reminder_advance=30,  # minutes
        default_timer_duration=300,  # seconds
        preferred_calculator_mode="scientific",
        preferred_unit_system="metric"
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)

    assert preference.id is not None
    assert preference.default_reminder_advance == 30
    assert preference.preferred_unit_system == "metric"

def test_utilities_service_reminders(db: Session, test_user: dict):
    """Test the utilities service reminder functionality."""
    service = UtilitiesService(db)
    
    # Create reminder
    reminder = service.create_reminder(
        user_id=1,
        title="Test Reminder",
        description="Test Description",
        due_date=datetime.utcnow() + timedelta(days=1)
    )
    assert reminder.title == "Test Reminder"

    # Get upcoming reminders
    upcoming = service.get_upcoming_reminders(user_id=1)
    assert len(upcoming) == 1
    assert upcoming[0].title == "Test Reminder"

def test_utilities_service_timers(db: Session, test_user: dict):
    """Test the utilities service timer functionality."""
    service = UtilitiesService(db)

    # Create timer
    timer = service.create_timer(
        user_id=1,
        name="Test Timer",
        duration=300
    )
    assert timer.name == "Test Timer"
    assert timer.duration == 300

    # Get active timers
    active_timers = service.get_active_timers(user_id=1)
    assert len(active_timers) == 1

def test_utilities_service_notes(db: Session, test_user: dict):
    """Test the utilities service notes functionality."""
    service = UtilitiesService(db)

    # Create note
    note = service.create_note(
        user_id=1,
        title="Test Note",
        content="Test Content"
    )
    assert note.title == "Test Note"

    # Get notes
    notes = service.get_notes(user_id=1)
    assert len(notes) == 1
    assert notes[0].content == "Test Content"

def test_utilities_service_calculator(db: Session, test_user: dict):
    """Test the utilities service calculator functionality."""
    service = UtilitiesService(db)

    # Perform calculation
    result = service.calculate(
        user_id=1,
        expression="2 + 2"
    )
    assert result == "4"

    # Get calculation history
    history = service.get_calculator_history(user_id=1)
    assert len(history) == 1
    assert history[0].expression == "2 + 2"

def test_utilities_service_conversion(db: Session, test_user: dict):
    """Test the utilities service conversion functionality."""
    service = UtilitiesService(db)

    # Perform conversion
    result = service.convert(
        user_id=1,
        from_unit="km",
        to_unit="miles",
        value=10.0
    )
    assert abs(result - 6.21371) < 0.0001

    # Get conversion history
    history = service.get_conversion_history(user_id=1)
    assert len(history) == 1
    assert history[0].from_unit == "km" 