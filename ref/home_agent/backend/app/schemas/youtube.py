from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, constr

# Base schemas
class YouTubeVideoBase(BaseModel):
    youtube_id: str = Field(..., max_length=255)
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    channel_id: str = Field(..., max_length=255)
    channel_title: str = Field(..., max_length=255)
    thumbnail_url: Optional[HttpUrl] = None
    duration: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    published_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class YouTubePlaylistBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_public: bool = False

class YouTubeWatchRecordBase(BaseModel):
    watch_duration: Optional[int] = None
    completed: bool = False
    last_position: int = 0
    notes: Optional[str] = None

class YouTubePreferenceBase(BaseModel):
    preferred_channels: Optional[List[str]] = None
    preferred_categories: Optional[List[str]] = None
    excluded_channels: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    autoplay_enabled: bool = True
    subtitle_language: Optional[str] = Field(None, max_length=10)
    quality_preference: str = Field("auto", max_length=20)

# Create schemas
class YouTubeVideoCreate(YouTubeVideoBase):
    pass

class YouTubePlaylistCreate(YouTubePlaylistBase):
    pass

class YouTubeWatchRecordCreate(YouTubeWatchRecordBase):
    video_id: int

class YouTubePreferenceCreate(YouTubePreferenceBase):
    pass

# Update schemas
class YouTubeVideoUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    thumbnail_url: Optional[HttpUrl] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class YouTubePlaylistUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None

class YouTubeWatchRecordUpdate(BaseModel):
    watch_duration: Optional[int] = None
    completed: Optional[bool] = None
    last_position: Optional[int] = None
    notes: Optional[str] = None

class YouTubePreferenceUpdate(BaseModel):
    preferred_channels: Optional[List[str]] = None
    preferred_categories: Optional[List[str]] = None
    excluded_channels: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    autoplay_enabled: Optional[bool] = None
    subtitle_language: Optional[str] = Field(None, max_length=10)
    quality_preference: Optional[str] = Field(None, max_length=20)

# Response schemas
class YouTubeVideo(YouTubeVideoBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    playlist_count: Optional[int] = None
    watch_count: Optional[int] = None

    class Config:
        from_attributes = True

class YouTubePlaylist(YouTubePlaylistBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    video_count: Optional[int] = None

    class Config:
        from_attributes = True

class YouTubeWatchRecord(YouTubeWatchRecordBase):
    id: int
    user_id: int
    video_id: int
    watched_at: datetime
    video: YouTubeVideo

    class Config:
        from_attributes = True

class YouTubePreference(YouTubePreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class YouTubeRecommendation(BaseModel):
    id: int
    user_id: int
    video: YouTubeVideo
    reason: Optional[str] = None
    score: Optional[float] = None
    is_dismissed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class YouTubePlaylistWithVideos(YouTubePlaylist):
    videos: List[YouTubeVideo] = []

    class Config:
        from_attributes = True

class YouTubeWatchHistory(BaseModel):
    total_videos: int
    total_duration: int  # Total watch time in seconds
    videos_completed: int
    watch_records: List[YouTubeWatchRecord]

class YouTubeStats(BaseModel):
    total_playlists: int
    total_videos_watched: int
    total_watch_time: int  # In seconds
    videos_completed: int
    average_completion_rate: float
    by_channel: Dict[str, int]  # channel_id: count
    by_category: Dict[str, int]  # category: count
    popular_videos: List[Dict[str, Any]]  # [{video_id: str, count: int}]
    watch_time_by_day: Dict[str, int]  # date: duration 