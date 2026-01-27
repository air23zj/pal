import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_upload_photo(client: TestClient, db: Session, test_user_token: str):
    """Test uploading a photo via API."""
    response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Test Photo",
            "metadata": '{"device": "iPhone 13", "resolution": "4032x3024"}'
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Photo"
    assert data["file_type"] == "image/jpeg"
    assert "metadata" in data

def test_get_photo(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving a photo via API."""
    # First upload a photo
    upload_response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Test Photo"
        }
    )
    photo_id = upload_response.json()["id"]

    # Then retrieve it
    response = client.get(
        f"/api/v1/photos/{photo_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == photo_id
    assert data["title"] == "Test Photo"

def test_update_photo(client: TestClient, db: Session, test_user_token: str):
    """Test updating a photo via API."""
    # First upload a photo
    upload_response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Test Photo"
        }
    )
    photo_id = upload_response.json()["id"]

    # Then update it
    response = client.put(
        f"/api/v1/photos/{photo_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Updated Photo",
            "metadata": {
                "location": "San Francisco"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Photo"
    assert data["metadata"]["location"] == "San Francisco"

def test_delete_photo(client: TestClient, db: Session, test_user_token: str):
    """Test deleting a photo via API."""
    # First upload a photo
    upload_response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Test Photo"
        }
    )
    photo_id = upload_response.json()["id"]

    # Then delete it
    response = client.delete(
        f"/api/v1/photos/{photo_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/photos/{photo_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert get_response.status_code == 404

def test_create_album(client: TestClient, db: Session, test_user_token: str):
    """Test creating a photo album via API."""
    response = client.post(
        "/api/v1/photos/albums",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Album",
            "description": "Test Description",
            "metadata": {
                "location": "San Francisco",
                "date_range": {
                    "start": "2023-06-01",
                    "end": "2023-06-15"
                }
            }
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Album"
    assert data["description"] == "Test Description"
    assert data["metadata"]["location"] == "San Francisco"

def test_add_photo_to_album(client: TestClient, db: Session, test_user_token: str):
    """Test adding a photo to an album via API."""
    # First create an album
    album_response = client.post(
        "/api/v1/photos/albums",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Album"
        }
    )
    album_id = album_response.json()["id"]

    # Then upload a photo
    photo_response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Test Photo"
        }
    )
    photo_id = photo_response.json()["id"]

    # Then add photo to album
    response = client.post(
        f"/api/v1/photos/albums/{album_id}/photos",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "photo_id": photo_id
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_get_album_photos(client: TestClient, db: Session, test_user_token: str):
    """Test getting photos in an album via API."""
    # First create an album and add a photo
    album_response = client.post(
        "/api/v1/photos/albums",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Album"
        }
    )
    album_id = album_response.json()["id"]

    photo_response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Test Photo"
        }
    )
    photo_id = photo_response.json()["id"]

    client.post(
        f"/api/v1/photos/albums/{album_id}/photos",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "photo_id": photo_id
        }
    )

    # Then get album photos
    response = client.get(
        f"/api/v1/photos/albums/{album_id}/photos",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == photo_id

def test_share_photo(client: TestClient, db: Session, test_user_token: str):
    """Test sharing a photo via API."""
    # First upload a photo
    upload_response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Test Photo"
        }
    )
    photo_id = upload_response.json()["id"]

    # Then share it
    response = client.post(
        f"/api/v1/photos/{photo_id}/share",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "shared_with": 2,
            "permission": "view",
            "is_public": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["permission"] == "view"
    assert data["is_public"] is False
    assert "share_link" in data

def test_add_photo_tags(client: TestClient, db: Session, test_user_token: str):
    """Test adding tags to a photo via API."""
    # First upload a photo
    upload_response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Test Photo"
        }
    )
    photo_id = upload_response.json()["id"]

    # Then add tags
    response = client.post(
        f"/api/v1/photos/{photo_id}/tags",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "tags": ["beach", "sunset"],
            "source": "manual"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(tag["name"] == "beach" for tag in data)

def test_search_photos(client: TestClient, db: Session, test_user_token: str):
    """Test searching photos via API."""
    # First upload photos with tags
    photo1_response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("beach.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Beach Day"
        }
    )
    photo1_id = photo1_response.json()["id"]

    client.post(
        f"/api/v1/photos/{photo1_id}/tags",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "tags": ["beach", "summer"],
            "source": "manual"
        }
    )

    # Then search photos
    response = client.get(
        "/api/v1/photos/search",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={"query": "beach"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Beach Day"

def test_get_photo_metadata(client: TestClient, db: Session, test_user_token: str):
    """Test getting photo metadata via API."""
    # First upload a photo
    upload_response = client.post(
        "/api/v1/photos/upload",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.jpg", b"test_content", "image/jpeg")
        },
        data={
            "title": "Test Photo",
            "metadata": '{"camera_make": "Apple", "camera_model": "iPhone 13"}'
        }
    )
    photo_id = upload_response.json()["id"]

    # Then get metadata
    response = client.get(
        f"/api/v1/photos/{photo_id}/metadata",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["camera_make"] == "Apple"
    assert data["camera_model"] == "iPhone 13" 