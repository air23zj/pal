import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_create_voice_memo(client: TestClient, db: Session, test_user_token: str):
    """Test creating a voice memo via API."""
    response = client.post(
        "/api/v1/voice-memos/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Memo",
            "duration": 120,
            "file_path": "/storage/memos/test.webm",
            "file_size": 1024 * 1024,
            "metadata": {
                "device": "iPhone",
                "format": "webm",
                "sample_rate": 44100
            }
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Memo"
    assert data["duration"] == 120

def test_get_voice_memo(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving a voice memo via API."""
    # First create a memo
    create_response = client.post(
        "/api/v1/voice-memos/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Memo",
            "duration": 120,
            "file_path": "/storage/memos/test.webm"
        }
    )
    memo_id = create_response.json()["id"]

    # Then retrieve it
    response = client.get(
        f"/api/v1/voice-memos/{memo_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == memo_id
    assert data["title"] == "Test Memo"

def test_update_voice_memo(client: TestClient, db: Session, test_user_token: str):
    """Test updating a voice memo via API."""
    # First create a memo
    create_response = client.post(
        "/api/v1/voice-memos/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Memo",
            "duration": 120,
            "file_path": "/storage/memos/test.webm"
        }
    )
    memo_id = create_response.json()["id"]

    # Then update it
    response = client.put(
        f"/api/v1/voice-memos/{memo_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Updated Memo"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Memo"

def test_delete_voice_memo(client: TestClient, db: Session, test_user_token: str):
    """Test deleting a voice memo via API."""
    # First create a memo
    create_response = client.post(
        "/api/v1/voice-memos/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Memo",
            "duration": 120,
            "file_path": "/storage/memos/test.webm"
        }
    )
    memo_id = create_response.json()["id"]

    # Then delete it
    response = client.delete(
        f"/api/v1/voice-memos/{memo_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/voice-memos/{memo_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert get_response.status_code == 404

def test_transcribe_voice_memo(client: TestClient, db: Session, test_user_token: str):
    """Test transcribing a voice memo via API."""
    # First create a memo
    create_response = client.post(
        "/api/v1/voice-memos/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Memo",
            "duration": 120,
            "file_path": "/storage/memos/test.webm"
        }
    )
    memo_id = create_response.json()["id"]

    # Then transcribe it
    response = client.post(
        f"/api/v1/voice-memos/{memo_id}/transcribe",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "language": "en"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    assert "text" in data

def test_share_voice_memo(client: TestClient, db: Session, test_user_token: str):
    """Test sharing a voice memo via API."""
    # First create a memo
    create_response = client.post(
        "/api/v1/voice-memos/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Memo",
            "duration": 120,
            "file_path": "/storage/memos/test.webm"
        }
    )
    memo_id = create_response.json()["id"]

    # Then share it
    response = client.post(
        f"/api/v1/voice-memos/{memo_id}/share",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "shared_with": 2,
            "permission": "view"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["permission"] == "view"
    assert data["shared_with"] == 2

def test_create_folder(client: TestClient, db: Session, test_user_token: str):
    """Test creating a voice memo folder via API."""
    response = client.post(
        "/api/v1/voice-memos/folders/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Folder",
            "description": "Test Description"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Folder"
    assert data["description"] == "Test Description"

def test_add_memo_to_folder(client: TestClient, db: Session, test_user_token: str):
    """Test adding a voice memo to a folder via API."""
    # First create a folder
    folder_response = client.post(
        "/api/v1/voice-memos/folders/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Folder"
        }
    )
    folder_id = folder_response.json()["id"]

    # Then create a memo
    memo_response = client.post(
        "/api/v1/voice-memos/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Memo",
            "duration": 120,
            "file_path": "/storage/memos/test.webm",
            "folder_id": folder_id
        }
    )
    assert memo_response.status_code == 201
    data = memo_response.json()
    assert data["folder_id"] == folder_id

def test_search_voice_memos(client: TestClient, db: Session, test_user_token: str):
    """Test searching voice memos via API."""
    # First create some memos with transcriptions
    client.post(
        "/api/v1/voice-memos/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Meeting Notes",
            "duration": 120,
            "file_path": "/storage/memos/meeting.webm"
        }
    )
    client.post(
        "/api/v1/voice-memos/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Shopping List",
            "duration": 60,
            "file_path": "/storage/memos/shopping.webm"
        }
    )

    # Then search for memos
    response = client.get(
        "/api/v1/voice-memos/search",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={"query": "meeting"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(memo["title"] == "Meeting Notes" for memo in data)

def test_get_shared_memos(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving shared voice memos via API."""
    response = client.get(
        "/api/v1/voice-memos/shared",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_folder_contents(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving folder contents via API."""
    # First create a folder
    folder_response = client.post(
        "/api/v1/voice-memos/folders/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Folder"
        }
    )
    folder_id = folder_response.json()["id"]

    response = client.get(
        f"/api/v1/voice-memos/folders/{folder_id}/contents",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "memos" in data
    assert isinstance(data["memos"], list) 