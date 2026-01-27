from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..core.database import Base

class CallStatus(str, enum.Enum):
    SCHEDULED = "scheduled"  # Future call
    WAITING = "waiting"      # Host waiting for participants
    ONGOING = "ongoing"      # Call in progress
    ENDED = "ended"         # Call completed
    CANCELLED = "cancelled" # Call cancelled
    FAILED = "failed"       # Technical failure

class ParticipantRole(str, enum.Enum):
    HOST = "host"
    CO_HOST = "co_host"
    PARTICIPANT = "participant"

class ParticipantStatus(str, enum.Enum):
    INVITED = "invited"     # Invitation sent
    ACCEPTED = "accepted"   # Accepted but not joined
    DECLINED = "declined"   # Declined invitation
    JOINED = "joined"       # Currently in call
    LEFT = "left"          # Left the call
    REMOVED = "removed"     # Removed from call

class VideoCall(Base):
    __tablename__ = "video_calls"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    meeting_link = Column(String, unique=True)  # Unique meeting URL
    meeting_id = Column(String, unique=True)    # Unique meeting ID
    password = Column(String, nullable=True)    # Optional meeting password
    scheduled_start = Column(DateTime)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    status = Column(Enum(CallStatus), default=CallStatus.SCHEDULED)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # Store recurrence rules
    max_participants = Column(Integer, default=10)
    settings = Column(JSON, nullable=True)  # Store call settings (video, audio, etc.)
    recording_url = Column(String, nullable=True)  # URL to call recording if enabled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    host = relationship("User", back_populates="hosted_calls", foreign_keys=[host_id])
    participants = relationship("CallParticipant", back_populates="call", cascade="all, delete-orphan")
    chat_messages = relationship("CallMessage", back_populates="call", cascade="all, delete-orphan")

class CallParticipant(Base):
    __tablename__ = "call_participants"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("video_calls.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(Enum(ParticipantRole), default=ParticipantRole.PARTICIPANT)
    status = Column(Enum(ParticipantStatus), default=ParticipantStatus.INVITED)
    join_time = Column(DateTime, nullable=True)
    leave_time = Column(DateTime, nullable=True)
    settings = Column(JSON, nullable=True)  # Individual participant settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    call = relationship("VideoCall", back_populates="participants")
    user = relationship("User", back_populates="call_participations")

class CallMessage(Base):
    __tablename__ = "call_messages"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("video_calls.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    is_system_message = Column(Boolean, default=False)  # For system notifications
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    call = relationship("VideoCall", back_populates="chat_messages")
    sender = relationship("User") 