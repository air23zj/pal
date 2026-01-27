import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.news import (
    NewsArticle,
    NewsSource,
    NewsCategory,
    NewsPreference,
    NewsBookmark
)
from app.services.news import NewsService

def test_create_news_article(db: Session):
    """Test creating a news article."""
    article = NewsArticle(
        title="Breaking News Story",
        content="This is the full article content...",
        summary="A brief summary of the news story",
        source_id=1,
        author="John Doe",
        published_at=datetime.utcnow(),
        url="https://example.com/news/123",
        image_url="https://example.com/images/123.jpg",
        categories=["technology", "business"],
        metadata={
            "word_count": 1200,
            "read_time": 5,  # minutes
            "sentiment": "positive",
            "keywords": ["tech", "innovation", "startup"]
        }
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    assert article.id is not None
    assert article.title == "Breaking News Story"
    assert len(article.categories) == 2
    assert article.metadata["word_count"] == 1200

def test_create_news_source(db: Session):
    """Test creating a news source."""
    source = NewsSource(
        name="Tech Daily",
        url="https://techdaily.com",
        description="Leading technology news source",
        language="en",
        country="US",
        reliability_score=0.95,
        categories=["technology", "science"],
        metadata={
            "update_frequency": "hourly",
            "article_count": 1000,
            "founded_year": 2010
        }
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    assert source.id is not None
    assert source.name == "Tech Daily"
    assert source.reliability_score == 0.95
    assert "technology" in source.categories

def test_create_news_category(db: Session):
    """Test creating a news category."""
    category = NewsCategory(
        name="Technology",
        description="Technology and innovation news",
        parent_category_id=None,
        metadata={
            "subcategories": ["AI", "Blockchain", "Cloud"],
            "article_count": 500,
            "trending_score": 0.8
        }
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    assert category.id is not None
    assert category.name == "Technology"
    assert len(category.metadata["subcategories"]) == 3

def test_create_news_preference(db: Session, test_user: dict):
    """Test creating news preferences."""
    preference = NewsPreference(
        user_id=1,
        preferred_categories=["technology", "business", "science"],
        preferred_sources=["Tech Daily", "Business Weekly"],
        excluded_sources=["Tabloid News"],
        update_frequency="daily",
        notification_settings={
            "breaking_news": True,
            "daily_digest": True,
            "recommended_stories": False
        },
        content_filters={
            "language": ["en"],
            "country": ["US", "UK"],
            "min_reliability_score": 0.8
        }
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)

    assert preference.id is not None
    assert len(preference.preferred_categories) == 3
    assert preference.notification_settings["breaking_news"] is True
    assert preference.content_filters["min_reliability_score"] == 0.8

def test_create_news_bookmark(db: Session, test_user: dict):
    """Test creating a news bookmark."""
    bookmark = NewsBookmark(
        user_id=1,
        article_id=1,
        bookmarked_at=datetime.utcnow(),
        notes="Important article about tech trends",
        tags=["AI", "trends", "future"],
        folder="Tech News",
        metadata={
            "read_status": "unread",
            "importance": "high",
            "share_count": 0
        }
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    assert bookmark.id is not None
    assert bookmark.notes == "Important article about tech trends"
    assert len(bookmark.tags) == 3
    assert bookmark.metadata["importance"] == "high"

def test_news_service_articles(db: Session):
    """Test news service article operations."""
    service = NewsService(db)
    
    # Create article
    article = service.create_article(
        title="Test Article",
        content="Test content",
        source_id=1,
        published_at=datetime.utcnow()
    )
    assert article.title == "Test Article"

    # Get article
    retrieved = service.get_article(article.id)
    assert retrieved.content == "Test content"

    # Update article
    updated = service.update_article(
        article.id,
        title="Updated Article"
    )
    assert updated.title == "Updated Article"

    # Delete article
    deleted = service.delete_article(article.id)
    assert deleted is True

def test_news_service_sources(db: Session):
    """Test news service source operations."""
    service = NewsService(db)

    # Add source
    source = service.add_source(
        name="Test Source",
        url="https://test.com",
        reliability_score=0.9
    )
    assert source.name == "Test Source"

    # Get sources
    sources = service.get_sources(category="technology")
    assert len(sources) > 0

def test_news_service_preferences(db: Session, test_user: dict):
    """Test news service preference operations."""
    service = NewsService(db)

    # Set preferences
    prefs = service.set_preferences(
        user_id=1,
        preferred_categories=["technology"],
        update_frequency="daily"
    )
    assert "technology" in prefs.preferred_categories

    # Get preferences
    retrieved = service.get_preferences(user_id=1)
    assert retrieved.update_frequency == "daily"

def test_news_service_bookmarks(db: Session, test_user: dict):
    """Test news service bookmark operations."""
    service = NewsService(db)

    # Create test article
    article = service.create_article(
        title="Test Article",
        content="Test content",
        source_id=1,
        published_at=datetime.utcnow()
    )

    # Add bookmark
    bookmark = service.add_bookmark(
        user_id=1,
        article_id=article.id,
        notes="Important article"
    )
    assert bookmark.notes == "Important article"

    # Get bookmarks
    bookmarks = service.get_bookmarks(user_id=1)
    assert len(bookmarks) == 1

def test_news_service_recommendations(db: Session, test_user: dict):
    """Test news service recommendation operations."""
    service = NewsService(db)

    # Get recommended articles
    recommendations = service.get_recommendations(
        user_id=1,
        limit=5
    )
    assert isinstance(recommendations, list)
    assert len(recommendations) <= 5

def test_news_service_search(db: Session):
    """Test news service search operations."""
    service = NewsService(db)

    # Create test articles
    service.create_article(
        title="AI Breakthrough",
        content="Major breakthrough in AI research",
        source_id=1,
        published_at=datetime.utcnow(),
        categories=["technology", "AI"]
    )
    service.create_article(
        title="Market Update",
        content="Latest market trends",
        source_id=1,
        published_at=datetime.utcnow(),
        categories=["business"]
    )

    # Search articles
    results = service.search_articles(
        query="AI",
        categories=["technology"]
    )
    assert len(results) == 1
    assert results[0].title == "AI Breakthrough" 