from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....services.voice_memo import VoiceMemoService
from ....schemas.voice_memo import (
    VoiceMemo,
    VoiceMemoCreate,
    VoiceMemoUpdate,
    VoiceMemoWithShares,
    VoiceMemoShare,
    VoiceMemoShareCreate,
    VoiceMemoStats,
    VoiceMemoUploadResponse,
    VoiceMemoCategory
)
from ...dependencies.auth import get_current_user
from ....schemas.user import User

router = APIRouter()

@router.post("/", response_model=VoiceMemoUploadResponse)
async def create_voice_memo(
    *,
    memo_in: VoiceMemoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new voice memo and get upload URL.
    """
    return VoiceMemoService.initiate_upload(db, current_user.id, memo_in)

@router.get("/", response_model=List[VoiceMemo])
def get_voice_memos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[VoiceMemoCategory] = None,
    is_favorite: Optional[bool] = None,
    search: Optional[str] = None,
    shared_only: bool = Query(False, description="Get only shared memos"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve voice memos with various filters.
    """
    memos = VoiceMemoService.get_voice_memos(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        category=category,
        is_favorite=is_favorite,
        search=search,
        shared_only=shared_only
    )
    return memos

@router.get("/{memo_id}", response_model=VoiceMemoWithShares)
def get_voice_memo(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific voice memo by ID.
    """
    memo = VoiceMemoService.get_voice_memo(db, current_user.id, memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="Voice memo not found")
    return memo

@router.put("/{memo_id}", response_model=VoiceMemo)
def update_voice_memo(
    *,
    memo_id: int,
    memo_in: VoiceMemoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update a voice memo.
    """
    memo = VoiceMemoService.update_voice_memo(
        db, current_user.id, memo_id, memo_in
    )
    if not memo:
        raise HTTPException(status_code=404, detail="Voice memo not found")
    return memo

@router.delete("/{memo_id}")
def delete_voice_memo(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a voice memo.
    """
    success = VoiceMemoService.delete_voice_memo(db, current_user.id, memo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Voice memo not found")
    return {"message": "Voice memo successfully deleted"}

@router.post("/{memo_id}/share", response_model=VoiceMemoShare)
def share_voice_memo(
    *,
    memo_id: int,
    share_in: VoiceMemoShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Share a voice memo with another user.
    """
    return VoiceMemoService.share_voice_memo(
        db, current_user.id, memo_id, share_in
    )

@router.delete("/{memo_id}/share/{user_id}")
def remove_share(
    memo_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Remove a share from a voice memo.
    """
    success = VoiceMemoService.remove_share(
        db, current_user.id, memo_id, user_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Share not found")
    return {"message": "Share successfully removed"}

@router.get("/stats/summary", response_model=VoiceMemoStats)
def get_voice_memo_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get comprehensive statistics about voice memos.
    """
    return VoiceMemoService.get_voice_memo_stats(db, current_user.id)

@router.get("/{memo_id}/download")
def get_download_url(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a download URL for a voice memo.
    """
    url = VoiceMemoService.get_download_url(db, current_user.id, memo_id)
    return {"download_url": url} 