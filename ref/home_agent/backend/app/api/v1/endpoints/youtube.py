from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.deps import get_current_user, get_db
from ....models.user import User
from ....services.youtube import YouTubeService
from ....schemas.youtube import (
    YouTubeVideo,
    YouTubePlaylist,
    YouTubePlaylistCreate,
    YouTubePlaylistUpdate,
    YouTubePlaylistWithVideos,
    YouTubeWatchRecord,
    YouTubeWatchRecordCreate,
    YouTubeWatchRecordUpdate,
    YouTubePreference,
    YouTubePreferenceUpdate,
    YouTubeRecommendation,
    YouTubeWatchHistory,
    YouTubeStats
)

router = APIRouter()

@router.get("/video/{video_id}", response_model=YouTubeVideo)
def get_video(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    video_id: str
) -> YouTubeVideo:
    """
    Get video details from YouTube.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.get_video_details(video_id)

@router.post("/playlists", response_model=YouTubePlaylist)
def create_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist: YouTubePlaylistCreate
) -> YouTubePlaylist:
    """
    Create a new playlist.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.create_playlist(current_user.id, playlist)

@router.get("/playlists", response_model=List[YouTubePlaylist])
def get_playlists(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> List[YouTubePlaylist]:
    """
    Get all playlists for the current user.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.get_user_playlists(current_user.id, skip=skip, limit=limit)

@router.get("/playlists/{playlist_id}", response_model=YouTubePlaylistWithVideos)
def get_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: int
) -> YouTubePlaylistWithVideos:
    """
    Get a specific playlist by ID.
    """
    youtube_service = YouTubeService(db)
    playlist = youtube_service.get_playlist(current_user.id, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist

@router.post("/playlists/{playlist_id}/videos/{video_id}", response_model=YouTubePlaylist)
def add_video_to_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: int,
    video_id: str
) -> YouTubePlaylist:
    """
    Add a video to a playlist.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.add_video_to_playlist(current_user.id, playlist_id, video_id)

@router.delete("/playlists/{playlist_id}/videos/{video_id}", response_model=YouTubePlaylist)
def remove_video_from_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: int,
    video_id: int
) -> YouTubePlaylist:
    """
    Remove a video from a playlist.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.remove_video_from_playlist(current_user.id, playlist_id, video_id)

@router.post("/watch-history", response_model=YouTubeWatchRecord)
def create_watch_record(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    record: YouTubeWatchRecordCreate
) -> YouTubeWatchRecord:
    """
    Create a watch record for a video.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.create_watch_record(current_user.id, record)

@router.get("/watch-history", response_model=YouTubeWatchHistory)
def get_watch_history(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
) -> YouTubeWatchHistory:
    """
    Get user's watch history.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.get_watch_history(current_user.id, skip=skip, limit=limit)

@router.get("/preferences", response_model=YouTubePreference)
def get_preferences(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> YouTubePreference:
    """
    Get user's YouTube preferences.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.get_or_create_preferences(current_user.id)

@router.put("/preferences", response_model=YouTubePreference)
def update_preferences(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    preferences: YouTubePreferenceUpdate
) -> YouTubePreference:
    """
    Update user's YouTube preferences.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.update_preferences(current_user.id, preferences.dict(exclude_unset=True))

@router.get("/recommendations", response_model=List[YouTubeRecommendation])
def get_recommendations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50)
) -> List[YouTubeRecommendation]:
    """
    Get video recommendations for the user.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.get_recommendations(current_user.id, limit=limit)

@router.get("/stats", response_model=YouTubeStats)
def get_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> YouTubeStats:
    """
    Get YouTube statistics for the user.
    """
    youtube_service = YouTubeService(db)
    return youtube_service.get_stats(current_user.id) 