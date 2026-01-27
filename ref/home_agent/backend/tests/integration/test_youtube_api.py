import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.youtube import YouTubeVideo, YouTubePlaylist

def test_create_playlist(client: TestClient, test_auth_headers: dict):
    """Test creating a new playlist."""
    playlist_data = {
        "name": "Test Playlist",
        "description": "Test Description",
        "is_public": True
    }
    response = client.post(
        "/api/v1/youtube/playlists/",
        json=playlist_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Playlist"
    assert data["is_public"] is True

def test_get_playlists(client: TestClient, test_auth_headers: dict):
    """Test retrieving user's playlists."""
    response = client.get(
        "/api/v1/youtube/playlists/",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_playlist(client: TestClient, db: Session, test_auth_headers: dict):
    """Test updating a playlist."""
    # Create a test playlist
    playlist = YouTubePlaylist(
        user_id=1,
        name="Original Name",
        description="Original Description",
        is_public=True
    )
    db.add(playlist)
    db.commit()
    db.refresh(playlist)

    # Update the playlist
    update_data = {
        "name": "Updated Name",
        "description": "Updated Description",
        "is_public": False
    }
    response = client.put(
        f"/api/v1/youtube/playlists/{playlist.id}",
        json=update_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["is_public"] is False

def test_delete_playlist(client: TestClient, db: Session, test_auth_headers: dict):
    """Test deleting a playlist."""
    # Create a test playlist
    playlist = YouTubePlaylist(
        user_id=1,
        name="Test Playlist",
        description="Test Description"
    )
    db.add(playlist)
    db.commit()
    db.refresh(playlist)

    response = client.delete(
        f"/api/v1/youtube/playlists/{playlist.id}",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    assert response.json() is True

def test_add_video_to_playlist(client: TestClient, db: Session, test_auth_headers: dict):
    """Test adding a video to a playlist."""
    # Create test playlist and video
    playlist = YouTubePlaylist(
        user_id=1,
        name="Test Playlist"
    )
    db.add(playlist)
    
    video = YouTubeVideo(
        video_id="test123",
        title="Test Video"
    )
    db.add(video)
    db.commit()

    response = client.post(
        f"/api/v1/youtube/playlists/{playlist.id}/videos/{video.video_id}",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    assert response.json() is True

def test_get_watch_history(client: TestClient, test_auth_headers: dict):
    """Test retrieving watch history."""
    response = client.get(
        "/api/v1/youtube/history",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_watch_record(client: TestClient, test_auth_headers: dict):
    """Test creating a watch record."""
    watch_data = {
        "video_id": "test123",
        "watch_duration": 120,
        "completed": False
    }
    response = client.post(
        "/api/v1/youtube/history",
        json=watch_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "test123"
    assert data["watch_duration"] == 120

def test_get_preferences(client: TestClient, test_auth_headers: dict):
    """Test retrieving user preferences."""
    response = client.get(
        "/api/v1/youtube/preferences",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "preferred_categories" in data
    assert "language" in data

def test_update_preferences(client: TestClient, test_auth_headers: dict):
    """Test updating user preferences."""
    preferences_data = {
        "preferred_categories": ["music", "tech"],
        "content_filters": ["family_friendly"],
        "language": "en",
        "max_video_duration": 3600
    }
    response = client.put(
        "/api/v1/youtube/preferences",
        json=preferences_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "music" in data["preferred_categories"]
    assert data["language"] == "en"

def test_get_recommendations(client: TestClient, test_auth_headers: dict):
    """Test getting video recommendations."""
    response = client.get(
        "/api/v1/youtube/recommendations",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_invalid_playlist_operations(client: TestClient, test_auth_headers: dict):
    """Test invalid playlist operations."""
    # Test creating playlist with invalid data
    invalid_data = {
        "name": "",  # Empty name should be invalid
        "is_public": True
    }
    response = client.post(
        "/api/v1/youtube/playlists/",
        json=invalid_data,
        headers=test_auth_headers
    )
    assert response.status_code == 422

    # Test accessing non-existent playlist
    response = client.get(
        "/api/v1/youtube/playlists/99999",
        headers=test_auth_headers
    )
    assert response.status_code == 404 