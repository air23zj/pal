import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_get_articles(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving news articles via API."""
    response = client.get(
        "/api/v1/news/articles",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={
            "category": "technology",
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    if len(data) > 0:
        assert "title" in data[0]
        assert "content" in data[0]

def test_get_article(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving a specific news article via API."""
    # First create an article
    create_response = client.post(
        "/api/v1/news/articles",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Article",
            "content": "Test content",
            "source_id": 1,
            "published_at": datetime.utcnow().isoformat()
        }
    )
    article_id = create_response.json()["id"]

    # Then retrieve it
    response = client.get(
        f"/api/v1/news/articles/{article_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == article_id
    assert data["title"] == "Test Article"

def test_create_article(client: TestClient, db: Session, test_user_token: str):
    """Test creating a news article via API."""
    response = client.post(
        "/api/v1/news/articles",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Breaking News",
            "content": "This is a breaking news story...",
            "summary": "Brief summary of the news",
            "source_id": 1,
            "author": "John Doe",
            "categories": ["technology", "business"],
            "metadata": {
                "word_count": 1200,
                "read_time": 5
            }
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Breaking News"
    assert len(data["categories"]) == 2
    assert data["metadata"]["word_count"] == 1200

def test_update_article(client: TestClient, db: Session, test_user_token: str):
    """Test updating a news article via API."""
    # First create an article
    create_response = client.post(
        "/api/v1/news/articles",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Article",
            "content": "Test content",
            "source_id": 1
        }
    )
    article_id = create_response.json()["id"]

    # Then update it
    response = client.put(
        f"/api/v1/news/articles/{article_id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Updated Article",
            "content": "Updated content"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Article"
    assert data["content"] == "Updated content"

def test_delete_article(client: TestClient, db: Session, test_user_token: str):
    """Test deleting a news article via API."""
    # First create an article
    create_response = client.post(
        "/api/v1/news/articles",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Article",
            "content": "Test content",
            "source_id": 1
        }
    )
    article_id = create_response.json()["id"]

    # Then delete it
    response = client.delete(
        f"/api/v1/news/articles/{article_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/news/articles/{article_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert get_response.status_code == 404

def test_get_sources(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving news sources via API."""
    response = client.get(
        "/api/v1/news/sources",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={
            "category": "technology"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "name" in data[0]
        assert "reliability_score" in data[0]

def test_add_source(client: TestClient, db: Session, test_user_token: str):
    """Test adding a news source via API."""
    response = client.post(
        "/api/v1/news/sources",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Tech News Daily",
            "url": "https://technewsdaily.com",
            "description": "Latest technology news",
            "language": "en",
            "country": "US",
            "reliability_score": 0.95,
            "categories": ["technology", "science"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tech News Daily"
    assert data["reliability_score"] == 0.95

def test_update_preferences(client: TestClient, db: Session, test_user_token: str):
    """Test updating news preferences via API."""
    response = client.put(
        "/api/v1/news/preferences",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "preferred_categories": ["technology", "business"],
            "preferred_sources": ["Tech Daily"],
            "update_frequency": "daily",
            "notification_settings": {
                "breaking_news": True,
                "daily_digest": True
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["preferred_categories"]) == 2
    assert data["update_frequency"] == "daily"
    assert data["notification_settings"]["breaking_news"] is True

def test_get_preferences(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving news preferences via API."""
    response = client.get(
        "/api/v1/news/preferences",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "preferred_categories" in data
    assert "notification_settings" in data

def test_bookmark_article(client: TestClient, db: Session, test_user_token: str):
    """Test bookmarking a news article via API."""
    # First create an article
    create_response = client.post(
        "/api/v1/news/articles",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "title": "Test Article",
            "content": "Test content",
            "source_id": 1
        }
    )
    article_id = create_response.json()["id"]

    # Then bookmark it
    response = client.post(
        f"/api/v1/news/bookmarks",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "article_id": article_id,
            "notes": "Important article",
            "tags": ["AI", "tech"],
            "folder": "Tech News"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["article_id"] == article_id
    assert len(data["tags"]) == 2

def test_get_bookmarks(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving bookmarked articles via API."""
    response = client.get(
        "/api/v1/news/bookmarks",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_recommendations(client: TestClient, db: Session, test_user_token: str):
    """Test retrieving news recommendations via API."""
    response = client.get(
        "/api/v1/news/recommendations",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={
            "limit": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5

def test_search_articles(client: TestClient, db: Session, test_user_token: str):
    """Test searching news articles via API."""
    response = client.get(
        "/api/v1/news/search",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={
            "query": "technology",
            "categories": ["technology"],
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10 