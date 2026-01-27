from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

class VoiceMemoStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"

class VoiceMemoCategory(str, Enum):
    NOTE = "note"
    REMINDER = "reminder"
    TASK = "task"
    IDEA = "idea"
    MEETING = "meeting"
    CUSTOM = "custom"

class VoiceMemoShareBase(BaseModel):
    can_edit: bool = Field(default=False)
    expires_at: Optional[datetime] = None

class VoiceMemoShareCreate(VoiceMemoShareBase):
    shared_with_id: int

class VoiceMemoShare(VoiceMemoShareBase):
    id: int
    voice_memo_id: int
    shared_with_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class VoiceMemoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: VoiceMemoCategory = Field(default=VoiceMemoCategory.NOTE)
    duration: float = Field(..., ge=0)  # Duration in seconds
    file_format: str = Field(..., regex="^(mp3|wav|m4a|ogg)$")
    is_favorite: bool = Field(default=False)
    tags: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

class VoiceMemoCreate(VoiceMemoBase):
    file_size: int = Field(..., gt=0)  # Size in bytes

class VoiceMemoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[VoiceMemoCategory] = None
    is_favorite: Optional[bool] = None
    tags: Optional[str] = None

class VoiceMemo(VoiceMemoBase):
    id: int
    owner_id: int
    file_path: str
    file_size: int
    status: VoiceMemoStatus
    transcription: Optional[str] = None
    transcription_status: Optional[VoiceMemoStatus] = None
    created_at: datetime
    updated_at: datetime
    last_played_at: Optional[datetime] = None
    shares: List[VoiceMemoShare] = []

    class Config:
        from_attributes = True

class VoiceMemoWithShares(VoiceMemo):
    shared_with: List[Dict] = []  # List of users the memo is shared with

class VoiceMemoStats(BaseModel):
    total_count: int
    total_duration: float  # Total duration in seconds
    total_size: int  # Total size in bytes
    by_category: Dict[VoiceMemoCategory, int]  # Count by category
    by_month: Dict[str, int]  # Count by month (YYYY-MM)
    favorite_count: int
    shared_count: int
    transcribed_count: int

class VoiceMemoUploadResponse(BaseModel):
    """Response after initiating a voice memo upload"""
    id: int
    upload_url: str  # Presigned URL for uploading the file
    expires_at: datetime  # When the upload URL expires 