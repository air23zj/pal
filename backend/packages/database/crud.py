"""
CRUD operations for database models
"""
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from typing import Optional, List
import json
import logging

from .models import User, BriefRun, BriefBundle, Item, ItemState, FeedbackEvent
from packages.shared.schemas import BriefBundle as BriefBundleSchema

logger = logging.getLogger(__name__)


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO timestamp string to datetime object.

    Handles both 'Z' suffix and '+00:00' timezone formats.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        datetime object with timezone info
    """
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1] + '+00:00'
    return datetime.fromisoformat(timestamp_str)


# ============================================================================
# User Operations
# ============================================================================

def get_or_create_user(db: Session, user_id: str, timezone: str = "UTC") -> User:
    """
    Get existing user or create new one.

    Handles race conditions by catching IntegrityError and retrying.
    """
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        try:
            user = User(
                id=user_id,
                timezone=timezone,
                settings_json={},
                importance_weights_json={},
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except IntegrityError:
            # Race condition: another request created the user
            db.rollback()
            user = db.scalar(select(User).where(User.id == user_id))
            if not user:
                # Should not happen, but handle gracefully
                logger.error(f"Failed to get or create user: {user_id}")
                raise
    return user


def update_user_last_brief_timestamp(db: Session, user_id: str, timestamp: datetime) -> None:
    """Update user's last brief timestamp"""
    db.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_brief_timestamp_utc=timestamp)
    )
    db.commit()


# ============================================================================
# Brief Bundle Operations
# ============================================================================

def create_brief_bundle(db: Session, bundle: BriefBundleSchema) -> BriefBundle:
    """Create a new brief bundle"""
    generated_at = parse_iso_timestamp(bundle.generated_at_utc)

    db_bundle = BriefBundle(
        id=bundle.brief_id,
        user_id=bundle.user_id,
        brief_date_local=bundle.brief_date_local,
        generated_at_utc=generated_at,
        bundle_json=bundle.model_dump(mode='json'),
    )
    db.add(db_bundle)
    db.commit()
    db.refresh(db_bundle)

    # Update user's last brief timestamp
    update_user_last_brief_timestamp(db, bundle.user_id, generated_at)

    return db_bundle


def get_latest_brief(db: Session, user_id: str) -> Optional[BriefBundle]:
    """Get the most recent brief for a user"""
    return db.scalar(
        select(BriefBundle)
        .where(BriefBundle.user_id == user_id)
        .order_by(BriefBundle.generated_at_utc.desc())
    )


def get_brief_by_id(db: Session, brief_id: str) -> Optional[BriefBundle]:
    """Get a specific brief by ID"""
    return db.scalar(select(BriefBundle).where(BriefBundle.id == brief_id))


def get_briefs_by_date_range(
    db: Session,
    user_id: str,
    start_date: str,
    end_date: str
) -> List[BriefBundle]:
    """Get briefs within a date range"""
    return list(
        db.scalars(
            select(BriefBundle)
            .where(
                BriefBundle.user_id == user_id,
                BriefBundle.brief_date_local >= start_date,
                BriefBundle.brief_date_local <= end_date,
            )
            .order_by(BriefBundle.generated_at_utc.desc())
        ).all()
    )


# ============================================================================
# Brief Run Operations
# ============================================================================

def create_brief_run(
    db: Session,
    user_id: str,
    since_timestamp: datetime,
    status: str = "queued"
) -> BriefRun:
    """Create a new brief run"""
    run = BriefRun(
        user_id=user_id,
        status=status,
        since_timestamp_utc=since_timestamp,
        warnings_json=[],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_brief_run_status(
    db: Session,
    run_id: int,
    status: str,
    latency_ms: Optional[int] = None,
    cost_usd: Optional[float] = None,
    warnings: Optional[List[str]] = None,
) -> None:
    """Update brief run status"""
    update_data = {"status": status}
    if latency_ms is not None:
        update_data["latency_ms"] = latency_ms
    if cost_usd is not None:
        update_data["cost_estimate_usd"] = cost_usd
    if warnings is not None:
        update_data["warnings_json"] = warnings
    
    db.execute(
        update(BriefRun)
        .where(BriefRun.id == run_id)
        .values(**update_data)
    )
    db.commit()


def get_brief_run(db: Session, run_id: int) -> Optional[BriefRun]:
    """Get a brief run by ID"""
    return db.get(BriefRun, run_id)


# ============================================================================
# Item Operations
# ============================================================================

def create_or_update_item(
    db: Session,
    item_id: str,
    user_id: str,
    source: str,
    type: str,
    timestamp: datetime,
    title: str,
    summary: Optional[str] = None,
    source_id: Optional[str] = None,
    entity_keys: Optional[List[str]] = None,
    url: Optional[str] = None,
) -> Item:
    """Create or update an item"""
    item = db.get(Item, (item_id, user_id))
    
    if item:
        # Update existing
        item.title = title
        item.summary = summary
        item.url = url
        item.entity_keys_json = entity_keys or []
        item.timestamp_utc = timestamp
    else:
        # Create new
        item = Item(
            id=item_id,
            user_id=user_id,
            source=source,
            type=type,
            source_id=source_id,
            timestamp_utc=timestamp,
            title=title,
            summary=summary,
            entity_keys_json=entity_keys or [],
            url=url,
        )
        db.add(item)
    
    db.commit()
    db.refresh(item)
    return item


def get_item(db: Session, user_id: str, item_id: str) -> Optional[Item]:
    """Get an item by ID for a specific user"""
    return db.get(Item, (item_id, user_id))


# ============================================================================
# Item State Operations
# ============================================================================

def create_or_update_item_state(
    db: Session,
    user_id: str,
    item_id: str,
    state: str = "new",
    opened: bool = False,
    saved: bool = False,
    feedback_score: Optional[float] = None,
) -> ItemState:
    """Create or update item state"""
    now = datetime.now(timezone.utc)
    item_state = db.get(ItemState, (user_id, item_id))
    
    if item_state:
        # Update existing
        item_state.state = state
        item_state.last_seen_utc = now
        if opened:
            item_state.opened_count += 1
        if saved:
            item_state.saved_bool = True
        if feedback_score is not None:
            item_state.feedback_score = feedback_score
    else:
        # Create new
        item_state = ItemState(
            user_id=user_id,
            item_id=item_id,
            state=state,
            first_seen_utc=now,
            last_seen_utc=now,
            opened_count=1 if opened else 0,
            saved_bool=saved,
            feedback_score=feedback_score,
        )
        db.add(item_state)
    
    db.commit()
    db.refresh(item_state)
    return item_state


def get_item_state(db: Session, user_id: str, item_id: str) -> Optional[ItemState]:
    """Get item state"""
    return db.get(ItemState, (user_id, item_id))


# ============================================================================
# Feedback Operations
# ============================================================================

def create_feedback_event(
    db: Session,
    user_id: str,
    item_id: str,
    event_type: str,
    payload: Optional[dict] = None,
) -> FeedbackEvent:
    """Record a feedback event"""
    event = FeedbackEvent(
        user_id=user_id,
        item_id=item_id,
        event_type=event_type,
        payload_json=payload or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Update item state based on event type
    if event_type == "mark_seen":
        create_or_update_item_state(db, user_id, item_id, state="seen")
    elif event_type == "save":
        create_or_update_item_state(db, user_id, item_id, saved=True)
    elif event_type == "open":
        create_or_update_item_state(db, user_id, item_id, opened=True)
    elif event_type == "thumb_up":
        create_or_update_item_state(db, user_id, item_id, feedback_score=1.0)
    elif event_type == "thumb_down":
        create_or_update_item_state(db, user_id, item_id, feedback_score=-1.0)
    
    return event


def get_feedback_events(
    db: Session,
    user_id: str,
    limit: int = 100
) -> List[FeedbackEvent]:
    """Get recent feedback events for a user"""
    return list(
        db.scalars(
            select(FeedbackEvent)
            .where(FeedbackEvent.user_id == user_id)
            .order_by(FeedbackEvent.created_at_utc.desc())
            .limit(limit)
        ).all()
    )
