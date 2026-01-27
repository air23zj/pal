from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from ..db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Health relationships
    weight_records = relationship("WeightRecord", back_populates="user", cascade="all, delete-orphan")
    blood_pressure_records = relationship("BloodPressureRecord", back_populates="user", cascade="all, delete-orphan")
    exercise_goals = relationship("ExerciseGoal", back_populates="user", cascade="all, delete-orphan")
    heart_rate_records = relationship("HeartRateRecord", back_populates="user", cascade="all, delete-orphan")
    height_records = relationship("HeightRecord", back_populates="user", cascade="all, delete-orphan")
    doctor_visits = relationship("DoctorVisit", back_populates="user", cascade="all, delete-orphan")
    dietary_goals = relationship("DietaryGoal", back_populates="user", cascade="all, delete-orphan")

    # Weather relationships
    locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")

    # Voice memo relationships
    voice_memos = relationship("VoiceMemo", back_populates="owner", cascade="all, delete-orphan")
    shared_voice_memos = relationship("VoiceMemoShare", back_populates="shared_with", cascade="all, delete-orphan")

    # Video call relationships
    hosted_calls = relationship("VideoCall", back_populates="host", foreign_keys="[VideoCall.host_id]", cascade="all, delete-orphan")
    call_participations = relationship("CallParticipant", back_populates="user", cascade="all, delete-orphan")
    call_messages = relationship("CallMessage", back_populates="author", cascade="all, delete-orphan")

    # Photo relationships
    photos = relationship("Photo", back_populates="owner", cascade="all, delete-orphan")
    albums = relationship("PhotoAlbum", back_populates="owner", cascade="all, delete-orphan")
    photo_comments = relationship("PhotoComment", back_populates="author", cascade="all, delete-orphan")
    photo_reactions = relationship("PhotoReaction", back_populates="user", cascade="all, delete-orphan")
    shared_photos = relationship("PhotoShare", back_populates="shared_with", cascade="all, delete-orphan")
    shared_albums = relationship("AlbumShare", back_populates="shared_with", cascade="all, delete-orphan")

    # Document relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    document_folders = relationship("DocumentFolder", back_populates="owner", cascade="all, delete-orphan")
    document_tags = relationship("DocumentTag", back_populates="owner", cascade="all, delete-orphan")
    shared_documents = relationship("DocumentShare", back_populates="shared_with", cascade="all, delete-orphan")
    shared_document_folders = relationship("DocumentFolderShare", back_populates="shared_with", cascade="all, delete-orphan")

    # News relationships
    news_preferences = relationship("NewsPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    news_bookmarks = relationship("NewsBookmark", back_populates="user", cascade="all, delete-orphan")
    news_read_records = relationship("NewsReadRecord", back_populates="user", cascade="all, delete-orphan")
    news_category_preferences = relationship(
        "NewsCategory",
        secondary="user_category_preference",
        back_populates="interested_users"
    )

    # Search relationships
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    search_settings = relationship("SearchSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # YouTube relationships
    youtube_playlists = relationship("YouTubePlaylist", back_populates="user", cascade="all, delete-orphan")
    youtube_watch_history = relationship("YouTubeWatchRecord", back_populates="user", cascade="all, delete-orphan")
    youtube_preferences = relationship("YouTubePreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    youtube_recommendations = relationship("YouTubeRecommendation", back_populates="user", cascade="all, delete-orphan")

    # Shopping relationships
    price_alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    shopping_lists = relationship("ShoppingList", back_populates="user", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="user", cascade="all, delete-orphan")
    shopping_preferences = relationship("ShoppingPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # Utilities relationships
    calculation_history = relationship("CalculationHistory", back_populates="user", cascade="all, delete-orphan")
    unit_conversion_preferences = relationship("UnitConversionPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    currency_preferences = relationship("CurrencyPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    timezone_preferences = relationship("TimeZonePreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    generated_content = relationship("GeneratedContent", back_populates="user", cascade="all, delete-orphan")
    file_conversions = relationship("FileConversion", back_populates="user", cascade="all, delete-orphan")