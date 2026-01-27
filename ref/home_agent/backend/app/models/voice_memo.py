from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..core.database import Base

class VoiceMemoStatus(str, enum.Enum):
    PENDING = "pending"  # Being uploaded/processed
    READY = "ready"     # Ready for playback
    FAILED = "failed"   # Processing failed
    DELETED = "deleted" # Marked for deletion but not physically deleted

class VoiceMemoCategory(str, enum.Enum):
    NOTE = "note"
    REMINDER = "reminder"
    TASK = "task"
    IDEA = "idea"
    MEETING = "meeting"
    CUSTOM = "custom"

class VoiceMemo(Base):
    __tablename__ = "voice_memos"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    category = Column(Enum(VoiceMemoCategory), default=VoiceMemoCategory.NOTE)
    duration = Column(Float)  # Duration in seconds
    file_path = Column(String)  # Path to the audio file
    file_size = Column(Integer)  # Size in bytes
    file_format = Column(String)  # Audio format (e.g., mp3, wav)
    status = Column(Enum(VoiceMemoStatus), default=VoiceMemoStatus.PENDING)
    is_favorite = Column(Boolean, default=False)
    transcription = Column(String, nullable=True)  # Optional transcription text
    transcription_status = Column(Enum(VoiceMemoStatus), nullable=True)  # Status of transcription
    tags = Column(String, nullable=True)  # Comma-separated tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    recorded_at = Column(DateTime, default=datetime.utcnow)  # When the memo was recorded
    last_played_at = Column(DateTime, nullable=True)  # When the memo was last played

    # Relationships
    owner = relationship("User", back_populates="voice_memos")
    shares = relationship("VoiceMemoShare", back_populates="voice_memo", cascade="all, delete-orphan")

class VoiceMemoShare(Base):
    __tablename__ = "voice_memo_shares"

    id = Column(Integer, primary_key=True, index=True)
    voice_memo_id = Column(Integer, ForeignKey("voice_memos.id"))
    shared_with_id = Column(Integer, ForeignKey("users.id"))
    can_edit = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration date

    # Relationships
    voice_memo = relationship("VoiceMemo", back_populates="shares")
    shared_with = relationship("User", foreign_keys=[shared_with_id]) 