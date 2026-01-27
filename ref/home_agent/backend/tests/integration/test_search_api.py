import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.search import SearchType, SearchIndex
from app.schemas.search import SearchRequest

def test_search_endpoint(client: TestClient, db: Session, test_auth_headers: dict):
    """Test the main search endpoint."""
    # Create test data
    search_index = SearchIndex(
        content_type=SearchType.DOCUMENT,
        content_id=1,
        title="Test Document",
        description="This is a test document",
        keywords=["test", "document"]
    )
    db.add(search_index)
    db.commit()

    # Make search request
    search_data = {
        "query": "test document",
        "search_type": "all",
        "page": 1,
        "per_page": 10
    }
    response = client.post(
        "/api/v1/search/",
        json=search_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test document"
    assert data["total_results"] >= 1
    assert len(data["results"]) >= 1

def test_search_history_endpoint(client: TestClient, test_auth_headers: dict):
    """Test the search history endpoint."""
    response = client.get(
        "/api/v1/search/history",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_clear_search_history(client: TestClient, test_auth_headers: dict):
    """Test clearing search history."""
    response = client.delete(
        "/api/v1/search/history",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    assert response.json() is True

def test_search_settings_endpoints(client: TestClient, test_auth_headers: dict):
    """Test the search settings endpoints."""
    # Test getting settings
    response = client.get(
        "/api/v1/search/settings",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    settings = response.json()
    assert settings["default_search_type"] == "all"

    # Test updating settings
    update_data = {
        "default_search_type": "document",
        "max_results_per_type": 20,
        "save_search_history": True,
        "personalized_results": True
    }
    response = client.put(
        "/api/v1/search/settings",
        json=update_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    updated_settings = response.json()
    assert updated_settings["default_search_type"] == "document"
    assert updated_settings["max_results_per_type"] == 20

def test_search_stats_endpoint(client: TestClient, test_auth_headers: dict):
    """Test the search statistics endpoint."""
    response = client.get(
        "/api/v1/search/stats",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    stats = response.json()
    assert "total_searches" in stats
    assert "searches_by_type" in stats
    assert "top_queries" in stats
    assert "average_results" in stats

def test_search_with_filters(client: TestClient, db: Session, test_auth_headers: dict):
    """Test search with filters."""
    # Create test data
    search_index = SearchIndex(
        content_type=SearchType.DOCUMENT,
        content_id=1,
        title="Test Document",
        description="Test description",
        metadata={"category": "test"}
    )
    db.add(search_index)
    db.commit()

    # Make search request with filters
    search_data = {
        "query": "test",
        "search_type": "document",
        "filters": {
            "categories": ["test"]
        }
    }
    response = client.post(
        "/api/v1/search/",
        json=search_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] >= 1
    assert len(data["results"]) >= 1

def test_invalid_search_request(client: TestClient, test_auth_headers: dict):
    """Test search with invalid request data."""
    # Test with empty query
    search_data = {
        "query": "",
        "search_type": "all"
    }
    response = client.post(
        "/api/v1/search/",
        json=search_data,
        headers=test_auth_headers
    )

    assert response.status_code == 422  # Validation error

    # Test with invalid search type
    search_data = {
        "query": "test",
        "search_type": "invalid_type"
    }
    response = client.post(
        "/api/v1/search/",
        json=search_data,
        headers=test_auth_headers
    )

    assert response.status_code == 422  # Validation error 