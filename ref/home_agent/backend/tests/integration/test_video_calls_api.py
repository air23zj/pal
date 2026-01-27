import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_schedule_call(client: TestClient, db: Session, test_user_token: str):
    """Test scheduling a video call via API."""
    response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Team Meeting",
            "scheduled_start": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "duration": 60,
            "settings": {
                "max_participants": 10,
                "enable_chat": True,
                "enable_recording": True,
                "waiting_room": True
            }
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Team Meeting"
    assert data["scheduled_duration"] == 60
    assert "meeting_link" in data
    assert data["settings"]["max_participants"] == 10

def test_get_call(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving a video call via API."""
    # First schedule a call
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    # Then retrieve it
    response = client.get(
        f"/api/v1/video-calls/{call_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == call_id
    assert data["title"] == "Test Call"

def test_update_call(client: TestClient, db: Session, test_user_token: str):
    """Test updating a video call via API."""
    # First schedule a call
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    # Then update it
    response = client.put(
        f"/api/v1/video-calls/{call_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Updated Call",
            "duration": 45
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Call"
    assert data["scheduled_duration"] == 45

def test_cancel_call(client: TestClient, db: Session, test_user_token: str):
    """Test canceling a video call via API."""
    # First schedule a call
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    # Then cancel it
    response = client.delete(
        f"/api/v1/video-calls/{call_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Verify it's canceled
    get_response = client.get(
        f"/api/v1/video-calls/{call_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert get_response.json()["status"] == "canceled"

def test_join_call(client: TestClient, db: Session, test_user_token: str):
    """Test joining a video call via API."""
    # First schedule a call
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": datetime.utcnow().isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    # Then join it
    response = client.post(
        f"/api/v1/video-calls/{call_id}/join",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "device_info": {
                "type": "desktop",
                "os": "macOS",
                "browser": "Chrome"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "connection_token" in data
    assert "turn_servers" in data

def test_leave_call(client: TestClient, db: Session, test_user_token: str):
    """Test leaving a video call via API."""
    # First schedule and join a call
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": datetime.utcnow().isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    client.post(
        f"/api/v1/video-calls/{call_id}/join",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "device_info": {
                "type": "desktop",
                "os": "macOS",
                "browser": "Chrome"
            }
        }
    )

    # Then leave it
    response = client.post(
        f"/api/v1/video-calls/{call_id}/leave",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_start_recording(client: TestClient, db: Session, test_user_token: str):
    """Test starting a call recording via API."""
    # First schedule a call
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": datetime.utcnow().isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    # Then start recording
    response = client.post(
        f"/api/v1/video-calls/{call_id}/recording/start",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "resolution": "1080p"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recording"
    assert data["resolution"] == "1080p"

def test_stop_recording(client: TestClient, db: Session, test_user_token: str):
    """Test stopping a call recording via API."""
    # First schedule a call and start recording
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": datetime.utcnow().isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    recording_response = client.post(
        f"/api/v1/video-calls/{call_id}/recording/start",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "resolution": "1080p"
        }
    )
    recording_id = recording_response.json()["id"]

    # Then stop recording
    response = client.post(
        f"/api/v1/video-calls/{call_id}/recording/{recording_id}/stop",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

def test_send_message(client: TestClient, db: Session, test_user_token: str):
    """Test sending a chat message via API."""
    # First schedule a call
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": datetime.utcnow().isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    # Then send a message
    response = client.post(
        f"/api/v1/video-calls/{call_id}/messages",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "content": "Hello everyone!",
            "type": "text"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hello everyone!"
    assert data["type"] == "text"

def test_get_messages(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving chat messages via API."""
    # First schedule a call and send a message
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": datetime.utcnow().isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    client.post(
        f"/api/v1/video-calls/{call_id}/messages",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "content": "Hello everyone!",
            "type": "text"
        }
    )

    # Then get messages
    response = client.get(
        f"/api/v1/video-calls/{call_id}/messages",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Hello everyone!"

def test_update_settings(client: TestClient, db: Session, test_user_token: str):
    """Test updating video call settings via API."""
    response = client.put(
        "/api/v1/video-calls/settings",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "default_meeting_length": 45,
            "preferred_video_quality": "high",
            "preferred_audio_quality": "high",
            "auto_recording": True,
            "default_meeting_settings": {
                "mute_on_entry": True,
                "waiting_room": True
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["default_meeting_length"] == 45
    assert data["preferred_video_quality"] == "high"
    assert data["default_meeting_settings"]["mute_on_entry"] is True

def test_get_call_stats(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving call statistics via API."""
    # First schedule a call with participants
    schedule_response = client.post(
        "/api/v1/video-calls/schedule",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Call",
            "scheduled_start": datetime.utcnow().isoformat(),
            "duration": 30
        }
    )
    call_id = schedule_response.json()["id"]

    # Then get statistics
    response = client.get(
        f"/api/v1/video-calls/{call_id}/stats",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "participant_count" in data
    assert "duration" in data
    assert "quality_metrics" in data 