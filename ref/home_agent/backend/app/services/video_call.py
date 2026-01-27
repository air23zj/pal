from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import uuid
import json
from fastapi import HTTPException
import boto3

from ..models.video_call import (
    VideoCall,
    CallParticipant,
    CallMessage,
    CallStatus,
    ParticipantRole,
    ParticipantStatus
)
from ..schemas.video_call import (
    VideoCallCreate,
    VideoCallUpdate,
    CallParticipantCreate,
    CallMessageCreate,
    CallStats,
    CallInviteResponse
)
from ..core.config import settings

class VideoCallService:
    @staticmethod
    def generate_meeting_id() -> str:
        """Generate a unique meeting ID"""
        return str(uuid.uuid4())[:8].upper()

    @staticmethod
    def generate_meeting_link(meeting_id: str) -> str:
        """Generate a meeting link from meeting ID"""
        return f"{settings.APP_URL}/call/{meeting_id}"

    @staticmethod
    def create_call(
        db: Session, user_id: int, call: VideoCallCreate
    ) -> VideoCall:
        """Create a new video call"""
        meeting_id = VideoCallService.generate_meeting_id()
        meeting_link = VideoCallService.generate_meeting_link(meeting_id)

        db_call = VideoCall(
            **call.model_dump(),
            host_id=user_id,
            meeting_id=meeting_id,
            meeting_link=meeting_link
        )

        # Add host as first participant
        host_participant = CallParticipant(
            user_id=user_id,
            role=ParticipantRole.HOST,
            status=ParticipantStatus.ACCEPTED
        )
        db_call.participants.append(host_participant)

        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        return db_call

    @staticmethod
    def get_calls(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        include_past: bool = False,
        status: Optional[CallStatus] = None,
        hosted_only: bool = False
    ) -> List[VideoCall]:
        """Get video calls for a user"""
        query = db.query(VideoCall)

        if hosted_only:
            query = query.filter(VideoCall.host_id == user_id)
        else:
            # Get calls where user is host or participant
            query = query.join(CallParticipant)\
                .filter(
                    or_(
                        VideoCall.host_id == user_id,
                        and_(
                            CallParticipant.user_id == user_id,
                            CallParticipant.status != ParticipantStatus.DECLINED
                        )
                    )
                )

        if not include_past:
            query = query.filter(
                or_(
                    VideoCall.status.in_([CallStatus.SCHEDULED, CallStatus.WAITING, CallStatus.ONGOING]),
                    VideoCall.scheduled_end > datetime.utcnow()
                )
            )

        if status:
            query = query.filter(VideoCall.status == status)

        return query.order_by(VideoCall.scheduled_start)\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_call(
        db: Session, user_id: int, call_id: int
    ) -> Optional[VideoCall]:
        """Get a specific video call"""
        return db.query(VideoCall)\
            .join(CallParticipant)\
            .filter(
                VideoCall.id == call_id,
                or_(
                    VideoCall.host_id == user_id,
                    and_(
                        CallParticipant.user_id == user_id,
                        CallParticipant.status != ParticipantStatus.DECLINED
                    )
                )
            )\
            .first()

    @staticmethod
    def update_call(
        db: Session, user_id: int, call_id: int, call: VideoCallUpdate
    ) -> Optional[VideoCall]:
        """Update a video call"""
        db_call = db.query(VideoCall)\
            .filter(
                VideoCall.id == call_id,
                VideoCall.host_id == user_id
            )\
            .first()

        if not db_call:
            return None

        update_data = call.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_call, field, value)

        db.commit()
        db.refresh(db_call)
        return db_call

    @staticmethod
    def delete_call(
        db: Session, user_id: int, call_id: int
    ) -> bool:
        """Delete a video call"""
        db_call = db.query(VideoCall)\
            .filter(
                VideoCall.id == call_id,
                VideoCall.host_id == user_id
            )\
            .first()

        if db_call:
            db.delete(db_call)
            db.commit()
            return True
        return False

    @staticmethod
    def add_participant(
        db: Session, user_id: int, call_id: int, participant: CallParticipantCreate
    ) -> CallParticipant:
        """Add a participant to a call"""
        db_call = VideoCallService.get_call(db, user_id, call_id)
        if not db_call:
            raise HTTPException(status_code=404, detail="Call not found")

        # Check if user is host or co-host
        user_role = next(
            (p.role for p in db_call.participants if p.user_id == user_id),
            None
        )
        if user_role not in [ParticipantRole.HOST, ParticipantRole.CO_HOST]:
            raise HTTPException(
                status_code=403,
                detail="Only hosts and co-hosts can add participants"
            )

        # Check if participant already exists
        existing = next(
            (p for p in db_call.participants if p.user_id == participant.user_id),
            None
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="User is already a participant"
            )

        db_participant = CallParticipant(
            call_id=call_id,
            **participant.model_dump()
        )
        db.add(db_participant)
        db.commit()
        db.refresh(db_participant)
        return db_participant

    @staticmethod
    def remove_participant(
        db: Session, user_id: int, call_id: int, participant_id: int
    ) -> bool:
        """Remove a participant from a call"""
        db_call = VideoCallService.get_call(db, user_id, call_id)
        if not db_call:
            return False

        # Check if user is host or co-host
        user_role = next(
            (p.role for p in db_call.participants if p.user_id == user_id),
            None
        )
        if user_role not in [ParticipantRole.HOST, ParticipantRole.CO_HOST]:
            raise HTTPException(
                status_code=403,
                detail="Only hosts and co-hosts can remove participants"
            )

        db_participant = db.query(CallParticipant)\
            .filter(
                CallParticipant.call_id == call_id,
                CallParticipant.user_id == participant_id
            )\
            .first()

        if db_participant:
            db.delete(db_participant)
            db.commit()
            return True
        return False

    @staticmethod
    def respond_to_invite(
        db: Session, user_id: int, call_id: int, status: ParticipantStatus
    ) -> CallInviteResponse:
        """Respond to a call invitation"""
        db_participant = db.query(CallParticipant)\
            .filter(
                CallParticipant.call_id == call_id,
                CallParticipant.user_id == user_id
            )\
            .first()

        if not db_participant:
            raise HTTPException(status_code=404, detail="Invitation not found")

        db_participant.status = status
        db_participant.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_participant)

        return CallInviteResponse(
            call_id=call_id,
            user_id=user_id,
            status=status,
            updated_at=db_participant.updated_at
        )

    @staticmethod
    def join_call(
        db: Session, user_id: int, call_id: int
    ) -> CallParticipant:
        """Join a video call"""
        db_participant = db.query(CallParticipant)\
            .filter(
                CallParticipant.call_id == call_id,
                CallParticipant.user_id == user_id
            )\
            .first()

        if not db_participant:
            raise HTTPException(status_code=404, detail="Not a participant of this call")

        if db_participant.status not in [ParticipantStatus.ACCEPTED, ParticipantStatus.LEFT]:
            raise HTTPException(status_code=400, detail="Cannot join call in current status")

        db_participant.status = ParticipantStatus.JOINED
        db_participant.join_time = datetime.utcnow()
        db_participant.leave_time = None
        db.commit()
        db.refresh(db_participant)

        # Update call status if this is the first join
        db_call = db.query(VideoCall).filter(VideoCall.id == call_id).first()
        if db_call.status == CallStatus.SCHEDULED:
            db_call.status = CallStatus.ONGOING
            db_call.actual_start = datetime.utcnow()
            db.commit()

        return db_participant

    @staticmethod
    def leave_call(
        db: Session, user_id: int, call_id: int
    ) -> CallParticipant:
        """Leave a video call"""
        db_participant = db.query(CallParticipant)\
            .filter(
                CallParticipant.call_id == call_id,
                CallParticipant.user_id == user_id
            )\
            .first()

        if not db_participant:
            raise HTTPException(status_code=404, detail="Not a participant of this call")

        if db_participant.status != ParticipantStatus.JOINED:
            raise HTTPException(status_code=400, detail="Not currently in call")

        db_participant.status = ParticipantStatus.LEFT
        db_participant.leave_time = datetime.utcnow()
        db.commit()
        db.refresh(db_participant)

        # Check if this was the last participant
        active_participants = db.query(CallParticipant)\
            .filter(
                CallParticipant.call_id == call_id,
                CallParticipant.status == ParticipantStatus.JOINED
            )\
            .count()

        if active_participants == 0:
            db_call = db.query(VideoCall).filter(VideoCall.id == call_id).first()
            db_call.status = CallStatus.ENDED
            db_call.actual_end = datetime.utcnow()
            db.commit()

        return db_participant

    @staticmethod
    def add_message(
        db: Session, user_id: int, call_id: int, message: CallMessageCreate
    ) -> CallMessage:
        """Add a chat message to a call"""
        db_participant = db.query(CallParticipant)\
            .filter(
                CallParticipant.call_id == call_id,
                CallParticipant.user_id == user_id,
                CallParticipant.status == ParticipantStatus.JOINED
            )\
            .first()

        if not db_participant:
            raise HTTPException(status_code=403, detail="Must be an active participant to send messages")

        db_message = CallMessage(
            call_id=call_id,
            sender_id=user_id,
            **message.model_dump()
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def get_call_stats(
        db: Session, user_id: int
    ) -> CallStats:
        """Get statistics about user's video calls"""
        # Get basic counts
        total_calls = db.query(func.count(VideoCall.id))\
            .filter(VideoCall.host_id == user_id)\
            .scalar()

        # Calculate total duration
        completed_calls = db.query(VideoCall)\
            .filter(
                VideoCall.host_id == user_id,
                VideoCall.actual_start.isnot(None),
                VideoCall.actual_end.isnot(None)
            )\
            .all()

        total_duration = sum(
            (call.actual_end - call.actual_start).total_seconds() / 60
            for call in completed_calls
        )

        # Get total participants
        total_participants = db.query(func.count(CallParticipant.id))\
            .join(VideoCall)\
            .filter(VideoCall.host_id == user_id)\
            .scalar()

        # Get counts by status
        status_counts = {}
        for status in CallStatus:
            count = db.query(func.count(VideoCall.id))\
                .filter(
                    VideoCall.host_id == user_id,
                    VideoCall.status == status
                )\
                .scalar()
            status_counts[status] = count

        # Get counts by month
        month_counts = {}
        results = db.query(
            func.date_trunc('month', VideoCall.created_at).label('month'),
            func.count(VideoCall.id)
        )\
            .filter(VideoCall.host_id == user_id)\
            .group_by('month')\
            .all()
        for month, count in results:
            month_key = month.strftime("%Y-%m")
            month_counts[month_key] = count

        # Calculate averages
        avg_duration = total_duration / len(completed_calls) if completed_calls else 0
        avg_participants = total_participants / total_calls if total_calls > 0 else 0

        return CallStats(
            total_calls=total_calls,
            total_duration=total_duration,
            total_participants=total_participants,
            by_status=status_counts,
            by_month=month_counts,
            avg_duration=avg_duration,
            avg_participants=avg_participants
        ) 