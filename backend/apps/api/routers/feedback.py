"""Feedback endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from packages.database import get_db, crud

router = APIRouter()


class FeedbackRequest(BaseModel):
    """Feedback request schema"""
    item_ref: str
    event_type: str  # thumb_up | thumb_down | dismiss | less_like_this | mark_seen | save | open
    payload: Optional[Dict[str, Any]] = None
    user_id: str = "u_dev"  # TODO: Get from auth


class MarkSeenRequest(BaseModel):
    """Mark item as seen request"""
    item_ref: str
    user_id: str = "u_dev"  # TODO: Get from auth


@router.post("/feedback")
async def record_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Record user feedback"""
    # Ensure user exists
    crud.get_or_create_user(db, user_id=feedback.user_id)
    
    # Check if item exists (optional - may be created later)
    item = crud.get_item(db, item_id=feedback.item_ref)
    if not item:
        # Create placeholder item (will be updated when brief is generated)
        crud.create_or_update_item(
            db,
            item_id=feedback.item_ref,
            user_id=feedback.user_id,
            source="unknown",
            type="unknown",
            timestamp=datetime.now(timezone.utc),
            title="Placeholder",
        )
    
    # Record feedback event
    event = crud.create_feedback_event(
        db,
        user_id=feedback.user_id,
        item_id=feedback.item_ref,
        event_type=feedback.event_type,
        payload=feedback.payload,
    )
    
    return {
        "status": "recorded",
        "event_id": event.id,
        "item_ref": feedback.item_ref,
        "event_type": feedback.event_type,
        "recorded_at": event.created_at_utc.isoformat(),
    }


@router.post("/item/mark_seen")
async def mark_item_seen(
    request: MarkSeenRequest,
    db: Session = Depends(get_db)
):
    """Mark an item as seen"""
    # Ensure user exists
    crud.get_or_create_user(db, user_id=request.user_id)
    
    # Check if item exists
    item = crud.get_item(db, item_id=request.item_ref)
    if not item:
        # Create placeholder item
        crud.create_or_update_item(
            db,
            item_id=request.item_ref,
            user_id=request.user_id,
            source="unknown",
            type="unknown",
            timestamp=datetime.now(timezone.utc),
            title="Placeholder",
        )
    
    # Record mark_seen event
    event = crud.create_feedback_event(
        db,
        user_id=request.user_id,
        item_id=request.item_ref,
        event_type="mark_seen",
    )
    
    return {
        "status": "marked_seen",
        "item_ref": request.item_ref,
        "marked_at": event.created_at_utc.isoformat(),
    }
