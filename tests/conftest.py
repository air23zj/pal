"""
Pytest configuration and shared fixtures
"""
import os
import sys
from datetime import datetime, timezone
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set test mode BEFORE importing database modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TESTING"] = "true"

from packages.database.models import Base, User
from packages.shared.schemas import (
    BriefItem, Entity, NoveltyInfo, RankingScores,
    Evidence, SuggestedAction
)


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine"""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test"""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user"""
    user = User(
        id="test_user_123",
        timezone="UTC"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_brief_item() -> BriefItem:
    """Create a sample BriefItem for testing"""
    now = datetime.now(timezone.utc)
    return BriefItem(
        item_ref="gmail_email_msg123",
        source="gmail",
        type="email",
        timestamp_utc=now.isoformat(),
        title="Test Email",
        summary="This is a test email summary",
        why_it_matters="Test importance",
        entities=[
            Entity(kind="person", key="john.doe@example.com"),
            Entity(kind="org", key="acme_corp")
        ],
        novelty=NoveltyInfo(
            label="NEW",
            reason="First time seeing this item",
            first_seen_utc=now.isoformat(),
        ),
        ranking=RankingScores(
            relevance_score=0.8,
            urgency_score=0.6,
            credibility_score=0.9,
            actionability_score=0.7,
            final_score=0.75
        ),
        evidence=[
            Evidence(
                kind="snippet",
                title="Email content",
                text="Original email content..."
            )
        ],
        suggested_actions=[
            SuggestedAction(
                type="reply",
                label="Reply to Email",
                payload={"message_id": "msg123"}
            )
        ],
    )


@pytest.fixture
def sample_gmail_message() -> dict:
    """Create a sample Gmail API message response"""
    return {
        "id": "msg123",
        "threadId": "thread123",
        "labelIds": ["INBOX", "IMPORTANT"],
        "snippet": "This is a test email...",
        "internalDate": "1705000000000",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "test@example.com"},
                {"name": "Subject", "value": "Test Subject"},
                {"name": "Date", "value": "Mon, 15 Jan 2024 10:00:00 +0000"}
            ],
            "body": {
                "data": "VGhpcyBpcyBhIHRlc3QgZW1haWw="  # Base64 encoded "This is a test email"
            }
        }
    }


@pytest.fixture
def sample_calendar_event() -> dict:
    """Create a sample Google Calendar API event"""
    return {
        "id": "event123",
        "summary": "Team Meeting",
        "description": "Weekly team sync",
        "start": {
            "dateTime": "2024-01-15T14:00:00Z",
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": "2024-01-15T15:00:00Z",
            "timeZone": "UTC"
        },
        "attendees": [
            {"email": "alice@example.com", "responseStatus": "accepted"},
            {"email": "bob@example.com", "responseStatus": "needsAction"}
        ],
        "location": "Conference Room A",
        "htmlLink": "https://calendar.google.com/event?eid=event123"
    }


@pytest.fixture
def sample_social_post() -> dict:
    """Create a sample social media post"""
    return {
        "id": "post123",
        "author": "tech_influencer",
        "content": "Excited to announce our new AI product launch! 🚀 #AI #Innovation",
        "timestamp": "2024-01-15T12:00:00Z",
        "url": "https://twitter.com/tech_influencer/status/post123",
        "metrics": {
            "likes": 1250,
            "retweets": 340,
            "replies": 89
        }
    }


@pytest.fixture
def sample_brief_items_for_ranking() -> list[BriefItem]:
    """Create a list of BriefItems with varying scores for ranking tests"""
    base_time = datetime.now(timezone.utc)
    base_time_str = base_time.isoformat()

    items = []

    # High urgency email
    items.append(BriefItem(
        item_ref="gmail_email_urgent1",
        source="gmail",
        type="email",
        timestamp_utc=base_time_str,
        title="URGENT: Server Down",
        summary="Production server is experiencing issues",
        why_it_matters="Critical system issue",
        entities=[Entity(kind="system", key="production-server")],
        novelty=NoveltyInfo(label="NEW", reason="First time seen", first_seen_utc=base_time_str),
        ranking=RankingScores(
            relevance_score=0.9,
            urgency_score=1.0,
            credibility_score=0.95,
            actionability_score=0.9,
            final_score=0.0  # Will be calculated
        ),
        evidence=[Evidence(kind="snippet", title="Server logs", text="Server logs show errors...")],
        suggested_actions=[]
    ))

    # Medium priority meeting
    items.append(BriefItem(
        item_ref="calendar_event_meeting1",
        source="calendar",
        type="event",
        timestamp_utc=base_time_str,
        title="Team Standup",
        summary="Daily standup meeting in 1 hour",
        why_it_matters="Regular team sync",
        entities=[Entity(kind="event", key="standup")],
        novelty=NoveltyInfo(label="REPEAT", reason="Seen before", first_seen_utc=base_time_str),
        ranking=RankingScores(
            relevance_score=0.6,
            urgency_score=0.5,
            credibility_score=1.0,
            actionability_score=0.3,
            final_score=0.0  # Will be calculated
        ),
        evidence=[Evidence(kind="snippet", title="Meeting", text="Recurring daily meeting")],
        suggested_actions=[]
    ))

    # Low priority social post
    items.append(BriefItem(
        item_ref="social_x_post1",
        source="social_x",
        type="social_post",
        timestamp_utc=base_time_str,
        title="Industry News",
        summary="Interesting article about tech trends",
        why_it_matters="Industry insight",
        entities=[Entity(kind="topic", key="technology")],
        novelty=NoveltyInfo(label="NEW", reason="First time seen", first_seen_utc=base_time_str),
        ranking=RankingScores(
            relevance_score=0.4,
            urgency_score=0.1,
            credibility_score=0.7,
            actionability_score=0.2,
            final_score=0.0  # Will be calculated
        ),
        evidence=[Evidence(kind="snippet", title="Article", text="Tech trends article...")],
        suggested_actions=[]
    ))

    return items
