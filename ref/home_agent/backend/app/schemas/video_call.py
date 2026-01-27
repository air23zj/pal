from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

class CallStatus(str, Enum):
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    ONGOING = "ongoing"
    ENDED = "ended"
    CANCELLED = "cancelled"
    FAILED = "failed"

class ParticipantRole(str, Enum):
    HOST = "host"
    CO_HOST = "co_host"
    PARTICIPANT = "participant"

class ParticipantStatus(str, Enum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    JOINED = "joined"
    LEFT = "left"
    REMOVED = "removed"

class CallSettings(BaseModel):
    enable_video: bool = True
    enable_audio: bool = True
    mute_on_join: bool = True
    enable_chat: bool = True
    enable_recording: bool = False
    waiting_room: bool = True
    allow_screen_share: bool = True
    allow_reactions: bool = True
    allow_raise_hand: bool = True
    allow_participant_unmute: bool = True

class RecurrencePattern(BaseModel):
    frequency: str = Field(..., regex="^(daily|weekly|monthly)$")
    interval: int = Field(1, ge=1, le=30)  # Every n days/weeks/months
    days_of_week: Optional[List[int]] = Field(None, min_items=1, max_items=7)  # 0=Monday
    end_date: Optional[datetime] = None
    occurrences: Optional[int] = Field(None, ge=1, le=50)

    @validator('days_of_week')
    def validate_days(cls, v):
        if v and not all(0 <= day <= 6 for day in v):
            raise ValueError("Days must be between 0 (Monday) and 6 (Sunday)")
        return v

class CallParticipantBase(BaseModel):
    role: ParticipantRole = Field(default=ParticipantRole.PARTICIPANT)
    settings: Optional[Dict[str, Any]] = None

class CallParticipantCreate(CallParticipantBase):
    user_id: int

class CallParticipant(CallParticipantBase):
    id: int
    call_id: int
    user_id: int
    status: ParticipantStatus
    join_time: Optional[datetime] = None
    leave_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CallMessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    is_system_message: bool = False

class CallMessageCreate(CallMessageBase):
    pass

class CallMessage(CallMessageBase):
    id: int
    call_id: int
    sender_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class VideoCallBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    scheduled_start: datetime
    scheduled_end: Optional[datetime] = None
    max_participants: int = Field(default=10, ge=2, le=100)
    password: Optional[str] = Field(None, min_length=4, max_length=20)
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    settings: CallSettings = Field(default_factory=CallSettings)

    @validator('scheduled_end')
    def validate_end_time(cls, v, values):
        if v and 'scheduled_start' in values and v <= values['scheduled_start']:
            raise ValueError("End time must be after start time")
        return v

    @validator('recurrence_pattern')
    def validate_recurrence(cls, v, values):
        if values.get('is_recurring') and not v:
            raise ValueError("Recurrence pattern is required for recurring calls")
        return v

class VideoCallCreate(VideoCallBase):
    pass

class VideoCallUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    max_participants: Optional[int] = Field(None, ge=2, le=100)
    password: Optional[str] = Field(None, min_length=4, max_length=20)
    settings: Optional[CallSettings] = None
    status: Optional[CallStatus] = None

class VideoCall(VideoCallBase):
    id: int
    host_id: int
    meeting_link: str
    meeting_id: str
    status: CallStatus
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    recording_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    participants: List[CallParticipant] = []
    chat_messages: List[CallMessage] = []

    class Config:
        from_attributes = True

class VideoCallSummary(BaseModel):
    id: int
    title: str
    host_id: int
    scheduled_start: datetime
    scheduled_end: Optional[datetime]
    status: CallStatus
    participant_count: int

class CallStats(BaseModel):
    total_calls: int
    total_duration: float  # In minutes
    total_participants: int
    by_status: Dict[CallStatus, int]
    by_month: Dict[str, int]  # Format: "YYYY-MM"
    avg_duration: float  # In minutes
    avg_participants: float

class CallInviteResponse(BaseModel):
    """Response when a participant accepts/declines an invitation"""
    call_id: int
    user_id: int
    status: ParticipantStatus
    updated_at: datetime 