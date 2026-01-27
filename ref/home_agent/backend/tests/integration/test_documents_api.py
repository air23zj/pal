import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_create_document(client: TestClient, db: Session, test_user_token: str):
    """Test creating a document via API."""
    response = client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Project Proposal",
            "metadata": '{"author": "John Doe", "word_count": 2500}'
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Project Proposal"
    assert data["file_type"] == "application/docx"
    assert data["metadata"]["word_count"] == 2500

def test_get_document(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving a document via API."""
    # First create a document
    create_response = client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Test Document"
        }
    )
    doc_id = create_response.json()["id"]

    # Then retrieve it
    response = client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["title"] == "Test Document"

def test_update_document(client: TestClient, db: Session, test_user_token: str):
    """Test updating a document via API."""
    # First create a document
    create_response = client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Test Document"
        }
    )
    doc_id = create_response.json()["id"]

    # Then update it
    response = client.put(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Updated Document",
            "metadata": {
                "author": "Jane Doe"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Document"
    assert data["metadata"]["author"] == "Jane Doe"

def test_delete_document(client: TestClient, db: Session, test_user_token: str):
    """Test deleting a document via API."""
    # First create a document
    create_response = client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Test Document"
        }
    )
    doc_id = create_response.json()["id"]

    # Then delete it
    response = client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert get_response.status_code == 404

def test_create_version(client: TestClient, db: Session, test_user_token: str):
    """Test creating a document version via API."""
    # First create a document
    create_response = client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Test Document"
        }
    )
    doc_id = create_response.json()["id"]

    # Then create a new version
    response = client.post(
        f"/api/v1/documents/{doc_id}/versions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test_v2.docx", b"updated_content", "application/docx")
        },
        data={
            "changes_summary": "Updated content and formatting"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["version_number"] == 2
    assert data["changes_summary"] == "Updated content and formatting"

def test_get_versions(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving document versions via API."""
    # First create a document with multiple versions
    create_response = client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Test Document"
        }
    )
    doc_id = create_response.json()["id"]

    client.post(
        f"/api/v1/documents/{doc_id}/versions",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test_v2.docx", b"updated_content", "application/docx")
        },
        data={
            "changes_summary": "Version 2"
        }
    )

    # Then get versions
    response = client.get(
        f"/api/v1/documents/{doc_id}/versions",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[1]["version_number"] == 2

def test_share_document(client: TestClient, db: Session, test_user_token: str):
    """Test sharing a document via API."""
    # First create a document
    create_response = client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Test Document"
        }
    )
    doc_id = create_response.json()["id"]

    # Then share it
    response = client.post(
        f"/api/v1/documents/{doc_id}/share",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "shared_with": 2,
            "permission": "view",
            "is_public": False,
            "password": "secure123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["permission"] == "view"
    assert data["is_public"] is False
    assert "share_link" in data

def test_create_folder(client: TestClient, db: Session, test_user_token: str):
    """Test creating a document folder via API."""
    response = client.post(
        "/api/v1/documents/folders",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Project Documents",
            "description": "All project-related documents",
            "is_shared": False
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Project Documents"
    assert data["is_shared"] is False

def test_add_to_folder(client: TestClient, db: Session, test_user_token: str):
    """Test adding a document to a folder via API."""
    # First create a folder
    folder_response = client.post(
        "/api/v1/documents/folders",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Folder"
        }
    )
    folder_id = folder_response.json()["id"]

    # Then create a document
    doc_response = client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Test Document"
        }
    )
    doc_id = doc_response.json()["id"]

    # Then add document to folder
    response = client.post(
        f"/api/v1/documents/folders/{folder_id}/documents",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "document_id": doc_id
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_get_folder_contents(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving folder contents via API."""
    # First create a folder and add a document
    folder_response = client.post(
        "/api/v1/documents/folders",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Folder"
        }
    )
    folder_id = folder_response.json()["id"]

    doc_response = client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("test.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Test Document",
            "folder_id": str(folder_id)
        }
    )

    # Then get folder contents
    response = client.get(
        f"/api/v1/documents/folders/{folder_id}/contents",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 1

def test_search_documents(client: TestClient, db: Session, test_user_token: str):
    """Test searching documents via API."""
    # First create some documents
    client.post(
        "/api/v1/documents/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        files={
            "file": ("project.docx", b"test_content", "application/docx")
        },
        data={
            "title": "Project Plan",
            "metadata": '{"tags": ["project", "planning"]}'
        }
    )

    # Then search documents
    response = client.get(
        "/api/v1/documents/search",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={
            "query": "project",
            "tags": ["project"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(doc["title"] == "Project Plan" for doc in data) 