from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base_class import Base

class SearchType(str, enum.Enum):
    ALL = "all"
    DOCUMENT = "document"
    PHOTO = "photo"
    VOICE_MEMO = "voice_memo"
    VIDEO_CALL = "video_call"
    SHOPPING = "shopping"
    NEWS = "news"
    YOUTUBE = "youtube"
    HEALTH = "health"

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(String(500), nullable=False)
    search_type = Column(Enum(SearchType), default=SearchType.ALL)
    filters = Column(JSON, nullable=True)  # Store search filters
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="search_history")

class SearchSettings(Base):
    __tablename__ = "search_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    default_search_type = Column(Enum(SearchType), default=SearchType.ALL)
    excluded_types = Column(JSON, nullable=True)  # List of SearchTypes to exclude
    max_results_per_type = Column(Integer, default=10)
    save_search_history = Column(Boolean, default=True)
    personalized_results = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="search_settings")

class SearchIndex(Base):
    __tablename__ = "search_index"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(Enum(SearchType), nullable=False)
    content_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)  # List of keywords
    metadata = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('content_type', 'content_id', name='uix_content'),
    ) 