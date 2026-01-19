"""
Database models for Morning Brief AGI
Based on implementation_spec.md Section 11
"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    JSON,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime, timezone

class Base(DeclarativeBase):
    """Base class for all models"""
    pass



class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    timezone = Column(String, default="UTC", nullable=False)
    settings_json = Column(JSON, default=dict)
    importance_weights_json = Column(JSON, default=dict)
    last_brief_timestamp_utc = Column(DateTime, nullable=True)
    
    # Relationships
    brief_runs = relationship("BriefRun", back_populates="user")
    brief_bundles = relationship("BriefBundle", back_populates="user")
    items = relationship("Item", back_populates="user")
    item_states = relationship("ItemState", back_populates="user")
    feedback_events = relationship("FeedbackEvent", back_populates="user")


class BriefRun(Base):
    """Brief run tracking"""
    __tablename__ = "brief_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, nullable=False)  # queued|running|ok|degraded|error
    since_timestamp_utc = Column(DateTime, nullable=False)
    generated_at_utc = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    cost_estimate_usd = Column(Float, nullable=True)
    warnings_json = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", back_populates="brief_runs")


class BriefBundle(Base):
    """Stored brief bundles"""
    __tablename__ = "brief_bundles"
    
    id = Column(String, primary_key=True)  # Same as brief_id
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    brief_date_local = Column(String, nullable=False, index=True)  # YYYY-MM-DD
    generated_at_utc = Column(DateTime, nullable=False, index=True)
    bundle_json = Column(JSON, nullable=False)  # Full BriefBundle serialized
    
    # Relationships
    user = relationship("User", back_populates="brief_bundles")


class Item(Base):
    """Content items (emails, posts, papers, etc.)"""
    __tablename__ = "items"
    
    id = Column(String, primary_key=True)  # Stable hash per user
    user_id = Column(String, ForeignKey("users.id"), primary_key=True, index=True)
    source = Column(String, nullable=False, index=True)  # arxiv, gmail, x, linkedin, etc.
    type = Column(String, nullable=False, index=True)  # paper, email, post, event, etc.
    source_id = Column(String, nullable=True, index=True)  # Original ID from source
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    entity_keys_json = Column(JSON, default=list)  # List of entity keys
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="items")
    item_states = relationship("ItemState", back_populates="item")
    feedback_events = relationship("FeedbackEvent", back_populates="item")


class ItemState(Base):
    """User-specific item state tracking"""
    __tablename__ = "item_states"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "item_id"],
            ["items.user_id", "items.id"],
        ),
    )
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    item_id = Column(String, primary_key=True)
    state = Column(String, nullable=False)  # new|updated|seen|ignored|saved
    first_seen_utc = Column(DateTime, nullable=False)
    last_seen_utc = Column(DateTime, nullable=False)
    opened_count = Column(Integer, default=0, nullable=False)
    saved_bool = Column(Boolean, default=False, nullable=False)
    feedback_score = Column(Float, nullable=True)  # -1 to 1
    
    # Relationships
    user = relationship("User", back_populates="item_states")
    item = relationship("Item", back_populates="item_states")


class FeedbackEvent(Base):
    """User feedback events"""
    __tablename__ = "feedback_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "item_id"],
            ["items.user_id", "items.id"],
        ),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)  # thumb_up|thumb_down|dismiss|less_like_this|mark_seen|save|open
    created_at_utc = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    payload_json = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="feedback_events")
    item = relationship("Item", back_populates="feedback_events")
