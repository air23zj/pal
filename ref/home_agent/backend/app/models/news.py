from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.base_class import Base

# Association table for user-category preferences
user_category_preference = Table(
    'user_category_preference',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('news_categories.id'), primary_key=True)
)

class NewsCategory(Base):
    __tablename__ = "news_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    interested_users = relationship(
        "User",
        secondary=user_category_preference,
        back_populates="news_category_preferences"
    )
    articles = relationship("NewsArticle", back_populates="category")

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    image_url = Column(String(500), nullable=True)
    category_id = Column(Integer, ForeignKey("news_categories.id"), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSON, nullable=True)

    # Relationships
    category = relationship("NewsCategory", back_populates="articles")
    bookmarks = relationship("NewsBookmark", back_populates="article", cascade="all, delete-orphan")
    read_records = relationship("NewsReadRecord", back_populates="article", cascade="all, delete-orphan")

class NewsPreference(Base):
    __tablename__ = "news_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    preferred_sources = Column(JSON, nullable=True)  # List of preferred news sources
    excluded_sources = Column(JSON, nullable=True)  # List of excluded news sources
    preferred_languages = Column(JSON, nullable=True)  # List of preferred languages
    notification_enabled = Column(Boolean, default=True)
    email_digest_enabled = Column(Boolean, default=False)
    email_digest_frequency = Column(String(20), default="daily")  # daily, weekly, monthly
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="news_preferences")

class NewsBookmark(Base):
    __tablename__ = "news_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="news_bookmarks")
    article = relationship("NewsArticle", back_populates="bookmarks")

class NewsReadRecord(Base):
    __tablename__ = "news_read_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False)
    read_at = Column(DateTime(timezone=True), server_default=func.now())
    read_duration = Column(Integer, nullable=True)  # Duration in seconds
    completed = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="news_read_records")
    article = relationship("NewsArticle", back_populates="read_records") 