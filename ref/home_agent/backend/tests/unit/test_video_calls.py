import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.video_calls import (
    VideoCall,
    VideoCallParticipant,
    VideoCallRecording,
    VideoCallSetting,
    VideoCallMessage
)
from app.services.video_calls import VideoCallService

def test_create_video_call(db: Session, test_user: dict):
    """Test creating a video call."""
    call = VideoCall(
        host_id=1,
        title="Team Meeting",
        scheduled_start=datetime.utcnow() + timedelta(hours=1),
        scheduled_duration=60,  # minutes
        meeting_link="https://meet.example.com/abc123",
        password="123456",
        is_recurring=False,
        settings={
            "max_participants": 10,
            "enable_chat": True,
            "enable_recording": True,
            "waiting_room": True
        }
    )
    db.add(call)
    db.commit()
    db.refresh(call)

    assert call.id is not None
    assert call.title == "Team Meeting"
    assert call.scheduled_duration == 60
    assert call.meeting_link == "https://meet.example.com/abc123"
    assert call.settings["max_participants"] == 10

def test_create_video_call_participant(db: Session):
    """Test creating a video call participant."""
    participant = VideoCallParticipant(
        call_id=1,
        user_id=2,
        role="attendee",
        join_time=datetime.utcnow(),
        leave_time=None,
        device_info={
            "type": "desktop",
            "os": "macOS",
            "browser": "Chrome"
        },
        connection_quality={
            "video_quality": "high",
            "audio_quality": "good",
            "network_strength": 85
        }
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)

    assert participant.id is not None
    assert participant.role == "attendee"
    assert participant.device_info["type"] == "desktop"
    assert participant.connection_quality["network_strength"] == 85

def test_create_video_call_recording(db: Session):
    """Test creating a video call recording."""
    recording = VideoCallRecording(
        call_id=1,
        file_path="/storage/recordings/meeting_123.mp4",
        file_size=1024 * 1024 * 100,  # 100MB
        duration=3600,  # 1 hour in seconds
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow() + timedelta(hours=1),
        format="mp4",
        resolution="1080p",
        metadata={
            "participants": ["John", "Alice"],
            "chapters": [
                {"time": 0, "title": "Introduction"},
                {"time": 1800, "title": "Discussion"}
            ]
        }
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)

    assert recording.id is not None
    assert recording.file_size == 1024 * 1024 * 100
    assert recording.format == "mp4"
    assert len(recording.metadata["participants"]) == 2

def test_create_video_call_setting(db: Session, test_user: dict):
    """Test creating video call settings."""
    setting = VideoCallSetting(
        user_id=1,
        default_meeting_length=60,
        preferred_video_quality="high",
        preferred_audio_quality="high",
        auto_recording=True,
        default_meeting_settings={
            "mute_on_entry": True,
            "waiting_room": True,
            "require_password": True,
            "allow_chat": True
        },
        notification_preferences={
            "before_meeting": 15,  # minutes
            "meeting_reminder": True,
            "missed_calls": True
        }
    )
    db.add(setting)
    db.commit()
    db.refresh(setting)

    assert setting.id is not None
    assert setting.default_meeting_length == 60
    assert setting.preferred_video_quality == "high"
    assert setting.default_meeting_settings["mute_on_entry"] is True

def test_create_video_call_message(db: Session):
    """Test creating a video call chat message."""
    message = VideoCallMessage(
        call_id=1,
        user_id=1,
        content="Hello everyone!",
        message_type="text",
        sent_at=datetime.utcnow(),
        is_private=False,
        recipient_id=None,
        metadata={
            "reactions": [],
            "edited": False
        }
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    assert message.id is not None
    assert message.content == "Hello everyone!"
    assert message.is_private is False
    assert message.metadata["edited"] is False

def test_video_call_service_scheduling(db: Session, test_user: dict):
    """Test video call service scheduling operations."""
    service = VideoCallService(db)
    
    # Schedule call
    call = service.schedule_call(
        host_id=1,
        title="Team Meeting",
        scheduled_start=datetime.utcnow() + timedelta(hours=1),
        duration=60
    )
    assert call.title == "Team Meeting"

    # Get call
    retrieved = service.get_call(call.id)
    assert retrieved.scheduled_duration == 60

    # Update call
    updated = service.update_call(
        call.id,
        title="Updated Meeting"
    )
    assert updated.title == "Updated Meeting"

    # Cancel call
    cancelled = service.cancel_call(call.id)
    assert cancelled is True

def test_video_call_service_participants(db: Session, test_user: dict):
    """Test video call service participant operations."""
    service = VideoCallService(db)

    # Create test call
    call = service.schedule_call(
        host_id=1,
        title="Test Call",
        scheduled_start=datetime.utcnow(),
        duration=30
    )

    # Add participant
    participant = service.add_participant(
        call_id=call.id,
        user_id=2,
        role="attendee"
    )
    assert participant.role == "attendee"

    # Get participants
    participants = service.get_participants(call.id)
    assert len(participants) == 1

def test_video_call_service_recordings(db: Session, test_user: dict):
    """Test video call service recording operations."""
    service = VideoCallService(db)

    # Create test call
    call = service.schedule_call(
        host_id=1,
        title="Test Call",
        scheduled_start=datetime.utcnow(),
        duration=30
    )

    # Start recording
    recording = service.start_recording(
        call_id=call.id,
        resolution="1080p"
    )
    assert recording.resolution == "1080p"

    # Stop recording
    stopped = service.stop_recording(recording.id)
    assert stopped is True

    # Get recordings
    recordings = service.get_recordings(call.id)
    assert len(recordings) == 1

def test_video_call_service_messages(db: Session, test_user: dict):
    """Test video call service message operations."""
    service = VideoCallService(db)

    # Create test call
    call = service.schedule_call(
        host_id=1,
        title="Test Call",
        scheduled_start=datetime.utcnow(),
        duration=30
    )

    # Send message
    message = service.send_message(
        call_id=call.id,
        user_id=1,
        content="Hello!"
    )
    assert message.content == "Hello!"

    # Get messages
    messages = service.get_messages(call.id)
    assert len(messages) == 1

def test_video_call_service_settings(db: Session, test_user: dict):
    """Test video call service settings operations."""
    service = VideoCallService(db)

    # Set settings
    settings = service.set_settings(
        user_id=1,
        default_meeting_length=45,
        preferred_video_quality="high",
        auto_recording=True
    )
    assert settings.default_meeting_length == 45
    assert settings.preferred_video_quality == "high"

    # Get settings
    retrieved = service.get_settings(user_id=1)
    assert retrieved.auto_recording is True

def test_video_call_service_stats(db: Session, test_user: dict):
    """Test video call service statistics operations."""
    service = VideoCallService(db)

    # Create test call with participants
    call = service.schedule_call(
        host_id=1,
        title="Test Call",
        scheduled_start=datetime.utcnow(),
        duration=30
    )
    service.add_participant(call_id=call.id, user_id=2)
    service.add_participant(call_id=call.id, user_id=3)

    # Get call statistics
    stats = service.get_call_stats(call.id)
    assert stats["participant_count"] == 2
    assert "duration" in stats
    assert "quality_metrics" in stats 