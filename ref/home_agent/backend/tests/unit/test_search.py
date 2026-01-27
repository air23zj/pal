import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.search import SearchType, SearchHistory, SearchSettings, SearchIndex
from app.schemas.search import SearchRequest, SearchResponse, SearchFilters
from app.services.search import SearchService

def test_create_search_history(db: Session, test_user: dict):
    """Test creating a search history record."""
    search_history = SearchHistory(
        user_id=1,
        query="test query",
        search_type=SearchType.ALL,
        results_count=10
    )
    db.add(search_history)
    db.commit()
    db.refresh(search_history)

    assert search_history.id is not None
    assert search_history.query == "test query"
    assert search_history.search_type == SearchType.ALL
    assert search_history.results_count == 10

def test_create_search_settings(db: Session, test_user: dict):
    """Test creating search settings."""
    search_settings = SearchSettings(
        user_id=1,
        default_search_type=SearchType.ALL,
        max_results_per_type=10,
        save_search_history=True,
        personalized_results=True
    )
    db.add(search_settings)
    db.commit()
    db.refresh(search_settings)

    assert search_settings.id is not None
    assert search_settings.default_search_type == SearchType.ALL
    assert search_settings.max_results_per_type == 10
    assert search_settings.save_search_history is True
    assert search_settings.personalized_results is True

def test_create_search_index(db: Session):
    """Test creating a search index entry."""
    search_index = SearchIndex(
        content_type=SearchType.DOCUMENT,
        content_id=1,
        title="Test Document",
        description="Test description",
        keywords=["test", "document"],
        metadata={"author": "test_user"}
    )
    db.add(search_index)
    db.commit()
    db.refresh(search_index)

    assert search_index.id is not None
    assert search_index.content_type == SearchType.DOCUMENT
    assert search_index.title == "Test Document"
    assert search_index.keywords == ["test", "document"]

def test_search_service(db: Session, test_user: dict):
    """Test the search service functionality."""
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

    # Initialize search service
    search_service = SearchService(db)

    # Create search request
    search_request = SearchRequest(
        query="test document",
        search_type=SearchType.ALL,
        page=1,
        per_page=10
    )

    # Perform search
    result = search_service.search(1, search_request)

    assert isinstance(result, SearchResponse)
    assert result.total_results >= 1
    assert len(result.results) >= 1
    assert result.query == "test document"

def test_search_filters(db: Session, test_user: dict):
    """Test search filters functionality."""
    # Create test data
    current_time = datetime.utcnow()
    search_index = SearchIndex(
        content_type=SearchType.DOCUMENT,
        content_id=1,
        title="Test Document",
        description="Test description",
        metadata={"category": "test"}
    )
    db.add(search_index)
    db.commit()

    # Initialize search service
    search_service = SearchService(db)

    # Create search request with filters
    filters = SearchFilters(
        date_from=current_time,
        categories=["test"]
    )
    search_request = SearchRequest(
        query="test",
        search_type=SearchType.DOCUMENT,
        filters=filters
    )

    # Perform search
    result = search_service.search(1, search_request)

    assert isinstance(result, SearchResponse)
    assert result.total_results >= 1

def test_search_settings_update(db: Session, test_user: dict):
    """Test updating search settings."""
    # Create initial settings
    search_service = SearchService(db)
    settings = search_service.get_or_create_settings(1)

    # Update settings
    settings.default_search_type = SearchType.DOCUMENT
    settings.max_results_per_type = 20
    db.commit()
    db.refresh(settings)

    assert settings.default_search_type == SearchType.DOCUMENT
    assert settings.max_results_per_type == 20 