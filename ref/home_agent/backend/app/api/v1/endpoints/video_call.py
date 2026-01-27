from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....services.video_call import VideoCallService
from ....schemas.video_call import (
    VideoCall,
    VideoCallCreate,
    VideoCallUpdate,
    VideoCallSummary,
    CallParticipant,
    CallParticipantCreate,
    CallMessage,
    CallMessageCreate,
    CallStats,
    CallInviteResponse,
    CallStatus,
    ParticipantStatus
)
from ...dependencies.auth import get_current_user
from ....schemas.user import User

router = APIRouter()

@router.post("/", response_model=VideoCall)
def create_call(
    *,
    call_in: VideoCallCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new video call.
    """
    return VideoCallService.create_call(db, current_user.id, call_in)

@router.get("/", response_model=List[VideoCallSummary])
def get_calls(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    include_past: bool = Query(False, description="Include past calls"),
    status: Optional[CallStatus] = None,
    hosted_only: bool = Query(False, description="Get only hosted calls"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve video calls with various filters.
    """
    calls = VideoCallService.get_calls(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        include_past=include_past,
        status=status,
        hosted_only=hosted_only
    )
    return [
        VideoCallSummary(
            id=call.id,
            title=call.title,
            host_id=call.host_id,
            scheduled_start=call.scheduled_start,
            scheduled_end=call.scheduled_end,
            status=call.status,
            participant_count=len(call.participants)
        )
        for call in calls
    ]

@router.get("/{call_id}", response_model=VideoCall)
def get_call(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific video call by ID.
    """
    call = VideoCallService.get_call(db, current_user.id, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Video call not found")
    return call

@router.put("/{call_id}", response_model=VideoCall)
def update_call(
    *,
    call_id: int,
    call_in: VideoCallUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update a video call.
    """
    call = VideoCallService.update_call(db, current_user.id, call_id, call_in)
    if not call:
        raise HTTPException(status_code=404, detail="Video call not found")
    return call

@router.delete("/{call_id}")
def delete_call(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a video call.
    """
    success = VideoCallService.delete_call(db, current_user.id, call_id)
    if not success:
        raise HTTPException(status_code=404, detail="Video call not found")
    return {"message": "Video call successfully deleted"}

@router.post("/{call_id}/participants", response_model=CallParticipant)
def add_participant(
    *,
    call_id: int,
    participant_in: CallParticipantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Add a participant to a call.
    """
    return VideoCallService.add_participant(
        db, current_user.id, call_id, participant_in
    )

@router.delete("/{call_id}/participants/{user_id}")
def remove_participant(
    call_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Remove a participant from a call.
    """
    success = VideoCallService.remove_participant(
        db, current_user.id, call_id, user_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Participant not found")
    return {"message": "Participant successfully removed"}

@router.post("/{call_id}/respond", response_model=CallInviteResponse)
def respond_to_invite(
    *,
    call_id: int,
    status: ParticipantStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Respond to a call invitation.
    """
    return VideoCallService.respond_to_invite(db, current_user.id, call_id, status)

@router.post("/{call_id}/join", response_model=CallParticipant)
def join_call(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Join a video call.
    """
    return VideoCallService.join_call(db, current_user.id, call_id)

@router.post("/{call_id}/leave", response_model=CallParticipant)
def leave_call(
    call_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Leave a video call.
    """
    return VideoCallService.leave_call(db, current_user.id, call_id)

@router.post("/{call_id}/messages", response_model=CallMessage)
def add_message(
    *,
    call_id: int,
    message_in: CallMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Add a chat message to a call.
    """
    return VideoCallService.add_message(db, current_user.id, call_id, message_in)

@router.get("/stats/summary", response_model=CallStats)
def get_call_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get comprehensive statistics about video calls.
    """
    return VideoCallService.get_call_stats(db, current_user.id) 