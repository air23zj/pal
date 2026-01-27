from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text, Table, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.base_class import Base

# Association table for playlist videos
playlist_video_association = Table(
    'playlist_video_association',
    Base.metadata,
    Column('playlist_id', Integer, ForeignKey('youtube_playlists.id', ondelete='CASCADE')),
    Column('video_id', Integer, ForeignKey('youtube_videos.id', ondelete='CASCADE'))
)

class YouTubeVideo(Base):
    __tablename__ = "youtube_videos"

    id = Column(Integer, primary_key=True, index=True)
    youtube_id = Column(String(255), nullable=False, index=True)  # YouTube's video ID
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    channel_id = Column(String(255), nullable=False)
    channel_title = Column(String(255), nullable=False)
    thumbnail_url = Column(String(1000), nullable=True)
    duration = Column(String(20), nullable=True)  # Duration in ISO 8601 format
    view_count = Column(Integer, nullable=True)
    like_count = Column(Integer, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False)
    metadata = Column(JSON, nullable=True)  # Additional video metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    playlists = relationship(
        "YouTubePlaylist",
        secondary=playlist_video_association,
        back_populates="videos"
    )
    watch_records = relationship("YouTubeWatchRecord", back_populates="video", cascade="all, delete-orphan")

class YouTubePlaylist(Base):
    __tablename__ = "youtube_playlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="youtube_playlists")
    videos = relationship(
        "YouTubeVideo",
        secondary=playlist_video_association,
        back_populates="playlists"
    )

class YouTubeWatchRecord(Base):
    __tablename__ = "youtube_watch_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    video_id = Column(Integer, ForeignKey('youtube_videos.id', ondelete='CASCADE'), nullable=False)
    watched_at = Column(DateTime(timezone=True), server_default=func.now())
    watch_duration = Column(Integer, nullable=True)  # Duration watched in seconds
    completed = Column(Boolean, default=False)
    last_position = Column(Integer, default=0)  # Last watched position in seconds
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="youtube_watch_history")
    video = relationship("YouTubeVideo", back_populates="watch_records")

class YouTubePreference(Base):
    __tablename__ = "youtube_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    preferred_channels = Column(JSON, nullable=True)  # List of preferred channel IDs
    preferred_categories = Column(JSON, nullable=True)  # List of preferred video categories
    excluded_channels = Column(JSON, nullable=True)  # List of channels to exclude
    excluded_keywords = Column(JSON, nullable=True)  # List of keywords to filter out
    autoplay_enabled = Column(Boolean, default=True)
    subtitle_language = Column(String(10), nullable=True)  # Preferred subtitle language code
    quality_preference = Column(String(20), default="auto")  # Preferred video quality
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="youtube_preferences")

class YouTubeRecommendation(Base):
    __tablename__ = "youtube_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    video_id = Column(Integer, ForeignKey('youtube_videos.id', ondelete='CASCADE'), nullable=False)
    reason = Column(String(255), nullable=True)  # Why this video was recommended
    score = Column(Float, nullable=True)  # Recommendation score
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="youtube_recommendations")
    video = relationship("YouTubeVideo") 