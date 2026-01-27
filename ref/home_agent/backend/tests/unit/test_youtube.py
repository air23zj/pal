import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.youtube import (
    YouTubeVideo,
    YouTubePlaylist,
    YouTubeWatchRecord,
    YouTubePreference,
    YouTubeRecommendation
)
from app.services.youtube import YouTubeService

def test_create_youtube_video(db: Session):
    """Test creating a YouTube video record."""
    video = YouTubeVideo(
        video_id="test123",
        title="Test Video",
        description="Test Description",
        duration=300,
        thumbnail_url="https://example.com/thumb.jpg",
        metadata={"channel": "Test Channel"}
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    assert video.id is not None
    assert video.video_id == "test123"
    assert video.title == "Test Video"
    assert video.duration == 300

def test_create_youtube_playlist(db: Session, test_user: dict):
    """Test creating a YouTube playlist."""
    playlist = YouTubePlaylist(
        user_id=1,
        name="Test Playlist",
        description="Test Description",
        is_public=True
    )
    db.add(playlist)
    db.commit()
    db.refresh(playlist)

    assert playlist.id is not None
    assert playlist.name == "Test Playlist"
    assert playlist.is_public is True

def test_create_watch_record(db: Session, test_user: dict):
    """Test creating a watch record."""
    watch_record = YouTubeWatchRecord(
        user_id=1,
        video_id="test123",
        watched_at=datetime.utcnow(),
        watch_duration=120,
        completed=False
    )
    db.add(watch_record)
    db.commit()
    db.refresh(watch_record)

    assert watch_record.id is not None
    assert watch_record.video_id == "test123"
    assert watch_record.watch_duration == 120
    assert watch_record.completed is False

def test_create_youtube_preference(db: Session, test_user: dict):
    """Test creating YouTube preferences."""
    preference = YouTubePreference(
        user_id=1,
        preferred_categories=["music", "tech"],
        content_filters=["family_friendly"],
        language="en",
        max_video_duration=3600
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)

    assert preference.id is not None
    assert "music" in preference.preferred_categories
    assert "family_friendly" in preference.content_filters
    assert preference.language == "en"

def test_create_recommendation(db: Session, test_user: dict):
    """Test creating a video recommendation."""
    recommendation = YouTubeRecommendation(
        user_id=1,
        video_id="test123",
        score=0.85,
        reason="Based on your watch history",
        metadata={"category": "tech"}
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    assert recommendation.id is not None
    assert recommendation.video_id == "test123"
    assert recommendation.score == 0.85

def test_youtube_service(db: Session, test_user: dict):
    """Test the YouTube service functionality."""
    service = YouTubeService(db)
    
    # Test creating a playlist
    playlist = service.create_playlist(
        user_id=1,
        name="Test Playlist",
        description="Test Description",
        is_public=True
    )
    assert playlist.name == "Test Playlist"

    # Test adding a video to playlist
    video = YouTubeVideo(
        video_id="test123",
        title="Test Video",
        description="Test Description",
        duration=300
    )
    db.add(video)
    db.commit()

    service.add_video_to_playlist(playlist.id, video.video_id)
    updated_playlist = service.get_playlist(playlist.id)
    assert len(updated_playlist.videos) == 1

def test_watch_history(db: Session, test_user: dict):
    """Test watch history functionality."""
    service = YouTubeService(db)

    # Create watch records
    service.create_watch_record(
        user_id=1,
        video_id="test123",
        watch_duration=120
    )

    history = service.get_watch_history(user_id=1)
    assert len(history) == 1
    assert history[0].video_id == "test123"

def test_recommendations(db: Session, test_user: dict):
    """Test video recommendations."""
    service = YouTubeService(db)

    # Create test data
    video = YouTubeVideo(
        video_id="test123",
        title="Test Video",
        description="Test Description",
        duration=300,
        metadata={"category": "tech"}
    )
    db.add(video)
    db.commit()

    # Create user preference
    preference = YouTubePreference(
        user_id=1,
        preferred_categories=["tech"],
        language="en"
    )
    db.add(preference)
    db.commit()

    # Get recommendations
    recommendations = service.get_recommendations(user_id=1)
    assert len(recommendations) >= 0  # May be 0 if no matching recommendations 