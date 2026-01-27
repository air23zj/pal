import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_add_location(client: TestClient, db: Session, test_user_token: str):
    """Test adding a weather location via API."""
    response = client.post(
        "/api/v1/weather/locations/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "is_default": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "San Francisco"
    assert data["latitude"] == 37.7749
    assert data["is_default"] is True

def test_get_location(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving a weather location via API."""
    # First create a location
    create_response = client.post(
        "/api/v1/weather/locations/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
    )
    location_id = create_response.json()["id"]

    # Then retrieve it
    response = client.get(
        f"/api/v1/weather/locations/{location_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == location_id
    assert data["name"] == "San Francisco"

def test_update_location(client: TestClient, db: Session, test_user_token: str):
    """Test updating a weather location via API."""
    # First create a location
    create_response = client.post(
        "/api/v1/weather/locations/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
    )
    location_id = create_response.json()["id"]

    # Then update it
    response = client.put(
        f"/api/v1/weather/locations/{location_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "SF",
            "is_default": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SF"
    assert data["is_default"] is True

def test_delete_location(client: TestClient, db: Session, test_user_token: str):
    """Test deleting a weather location via API."""
    # First create a location
    create_response = client.post(
        "/api/v1/weather/locations/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
    )
    location_id = create_response.json()["id"]

    # Then delete it
    response = client.delete(
        f"/api/v1/weather/locations/{location_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/weather/locations/{location_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert get_response.status_code == 404

def test_get_current_weather(client: TestClient, db: Session, test_user_token: str):
    """Test getting current weather via API."""
    # First create a location
    create_response = client.post(
        "/api/v1/weather/locations/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
    )
    location_id = create_response.json()["id"]

    # Then get current weather
    response = client.get(
        f"/api/v1/weather/locations/{location_id}/current",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "temperature" in data
    assert "description" in data
    assert "humidity" in data

def test_get_forecast(client: TestClient, db: Session, test_user_token: str):
    """Test getting weather forecast via API."""
    # First create a location
    create_response = client.post(
        "/api/v1/weather/locations/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
    )
    location_id = create_response.json()["id"]

    # Then get forecast
    response = client.get(
        f"/api/v1/weather/locations/{location_id}/forecast",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "temperature" in data[0]
    assert "description" in data[0]

def test_get_alerts(client: TestClient, db: Session, test_user_token: str):
    """Test getting weather alerts via API."""
    # First create a location
    create_response = client.post(
        "/api/v1/weather/locations/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
    )
    location_id = create_response.json()["id"]

    # Then get alerts
    response = client.get(
        f"/api/v1/weather/locations/{location_id}/alerts",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_set_preferences(client: TestClient, db: Session, test_user_token: str):
    """Test setting weather preferences via API."""
    response = client.post(
        "/api/v1/weather/preferences",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "miles_per_hour",
            "notification_enabled": True,
            "alert_types": ["tornado", "hurricane"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["temperature_unit"] == "fahrenheit"
    assert data["wind_speed_unit"] == "miles_per_hour"
    assert data["notification_enabled"] is True
    assert "tornado" in data["alert_types"]

def test_get_preferences(client: TestClient, db: Session, test_user_token: str):
    """Test getting weather preferences via API."""
    # First set preferences
    client.post(
        "/api/v1/weather/preferences",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "temperature_unit": "celsius",
            "wind_speed_unit": "meters_per_second",
            "notification_enabled": True,
            "alert_types": ["severe_thunderstorm", "flood"]
        }
    )

    # Then get preferences
    response = client.get(
        "/api/v1/weather/preferences",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["temperature_unit"] == "celsius"
    assert data["wind_speed_unit"] == "meters_per_second"
    assert "severe_thunderstorm" in data["alert_types"]

def test_search_locations(client: TestClient, db: Session, test_user_token: str):
    """Test searching weather locations via API."""
    response = client.get(
        "/api/v1/weather/search",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={"query": "San Francisco"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(loc["name"] == "San Francisco" for loc in data)

def test_refresh_weather_data(client: TestClient, db: Session, test_user_token: str):
    """Test refreshing weather data via API."""
    # First create a location
    create_response = client.post(
        "/api/v1/weather/locations/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
    )
    location_id = create_response.json()["id"]

    # Then refresh weather data
    response = client.post(
        f"/api/v1/weather/locations/{location_id}/refresh",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "last_updated" in data 