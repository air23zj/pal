import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.weather import (
    WeatherLocation,
    WeatherAlert,
    WeatherForecast,
    WeatherPreference
)
from app.services.weather import WeatherService

def test_create_weather_location(db: Session, test_user: dict):
    """Test creating a weather location."""
    location = WeatherLocation(
        user_id=1,
        name="San Francisco",
        latitude=37.7749,
        longitude=-122.4194,
        timezone="America/Los_Angeles",
        is_default=True
    )
    db.add(location)
    db.commit()
    db.refresh(location)

    assert location.id is not None
    assert location.name == "San Francisco"
    assert location.latitude == 37.7749
    assert location.longitude == -122.4194
    assert location.is_default is True

def test_create_weather_alert(db: Session):
    """Test creating a weather alert."""
    alert = WeatherAlert(
        location_id=1,
        type="severe_thunderstorm",
        severity="moderate",
        title="Thunderstorm Warning",
        description="Severe thunderstorm warning for San Francisco area",
        starts_at=datetime.utcnow(),
        ends_at=datetime.utcnow() + timedelta(hours=3),
        source="National Weather Service"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    assert alert.id is not None
    assert alert.type == "severe_thunderstorm"
    assert alert.severity == "moderate"
    assert alert.title == "Thunderstorm Warning"

def test_create_weather_forecast(db: Session):
    """Test creating a weather forecast."""
    forecast = WeatherForecast(
        location_id=1,
        timestamp=datetime.utcnow(),
        temperature=22.5,
        feels_like=23.0,
        humidity=65,
        pressure=1013,
        wind_speed=5.2,
        wind_direction=180,
        description="Partly cloudy",
        icon="02d",
        precipitation_probability=20
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)

    assert forecast.id is not None
    assert forecast.temperature == 22.5
    assert forecast.humidity == 65
    assert forecast.description == "Partly cloudy"

def test_create_weather_preference(db: Session, test_user: dict):
    """Test creating weather preferences."""
    preference = WeatherPreference(
        user_id=1,
        temperature_unit="celsius",
        wind_speed_unit="meters_per_second",
        notification_enabled=True,
        alert_types=["severe_thunderstorm", "flood", "hurricane"]
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)

    assert preference.id is not None
    assert preference.temperature_unit == "celsius"
    assert preference.notification_enabled is True
    assert "severe_thunderstorm" in preference.alert_types

def test_weather_service_location(db: Session, test_user: dict):
    """Test weather service location operations."""
    service = WeatherService(db)
    
    # Add location
    location = service.add_location(
        user_id=1,
        name="San Francisco",
        latitude=37.7749,
        longitude=-122.4194
    )
    assert location.name == "San Francisco"

    # Get location
    retrieved = service.get_location(location.id)
    assert retrieved.latitude == 37.7749

    # Update location
    updated = service.update_location(
        location.id,
        name="SF",
        is_default=True
    )
    assert updated.name == "SF"
    assert updated.is_default is True

    # Delete location
    deleted = service.delete_location(location.id)
    assert deleted is True

def test_weather_service_forecast(db: Session, test_user: dict):
    """Test weather service forecast operations."""
    service = WeatherService(db)

    # Create test location
    location = service.add_location(
        user_id=1,
        name="San Francisco",
        latitude=37.7749,
        longitude=-122.4194
    )

    # Get current weather
    current = service.get_current_weather(location.id)
    assert current.temperature is not None
    assert current.description is not None

    # Get forecast
    forecast = service.get_forecast(location.id)
    assert len(forecast) > 0
    assert all(f.temperature is not None for f in forecast)

def test_weather_service_alerts(db: Session, test_user: dict):
    """Test weather service alert operations."""
    service = WeatherService(db)

    # Create test location
    location = service.add_location(
        user_id=1,
        name="San Francisco",
        latitude=37.7749,
        longitude=-122.4194
    )

    # Get active alerts
    alerts = service.get_active_alerts(location.id)
    assert isinstance(alerts, list)

    # Create alert
    alert = service.create_alert(
        location_id=location.id,
        type="severe_thunderstorm",
        severity="moderate",
        title="Test Alert",
        description="Test Description",
        duration_hours=3
    )
    assert alert.title == "Test Alert"

def test_weather_service_preferences(db: Session, test_user: dict):
    """Test weather service preference operations."""
    service = WeatherService(db)

    # Set preferences
    prefs = service.set_preferences(
        user_id=1,
        temperature_unit="fahrenheit",
        wind_speed_unit="miles_per_hour",
        notification_enabled=True,
        alert_types=["tornado", "hurricane"]
    )
    assert prefs.temperature_unit == "fahrenheit"
    assert "tornado" in prefs.alert_types

    # Get preferences
    retrieved = service.get_preferences(user_id=1)
    assert retrieved.wind_speed_unit == "miles_per_hour"

def test_weather_service_notifications(db: Session, test_user: dict):
    """Test weather service notification operations."""
    service = WeatherService(db)

    # Create test location and alert
    location = service.add_location(
        user_id=1,
        name="San Francisco",
        latitude=37.7749,
        longitude=-122.4194
    )
    alert = service.create_alert(
        location_id=location.id,
        type="severe_thunderstorm",
        severity="moderate",
        title="Test Alert",
        description="Test Description",
        duration_hours=3
    )

    # Test notification check
    should_notify = service.should_notify_user(
        user_id=1,
        alert_id=alert.id
    )
    assert isinstance(should_notify, bool)

def test_weather_service_data_refresh(db: Session, test_user: dict):
    """Test weather service data refresh operations."""
    service = WeatherService(db)

    # Create test location
    location = service.add_location(
        user_id=1,
        name="San Francisco",
        latitude=37.7749,
        longitude=-122.4194
    )

    # Refresh weather data
    updated = service.refresh_weather_data(location.id)
    assert updated is True

    # Get last update time
    last_update = service.get_last_update_time(location.id)
    assert isinstance(last_update, datetime) 