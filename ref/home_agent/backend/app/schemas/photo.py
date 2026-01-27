from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class ReactionType(str, Enum):
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"

# Base schemas
class PhotoBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    file_type: str = Field(..., max_length=50)
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    location: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_favorite: bool = False
    is_private: bool = False

class PhotoAlbumBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_private: bool = False

class PhotoTagBase(BaseModel):
    name: str = Field(..., max_length=50)

class PhotoShareBase(BaseModel):
    shared_with_id: int
    can_edit: bool = False

class AlbumShareBase(BaseModel):
    shared_with_id: int
    can_edit: bool = False

class PhotoCommentBase(BaseModel):
    content: str

class PhotoReactionBase(BaseModel):
    reaction: ReactionType

# Create schemas
class PhotoCreate(PhotoBase):
    pass

class PhotoAlbumCreate(PhotoAlbumBase):
    pass

class PhotoTagCreate(PhotoTagBase):
    pass

class PhotoShareCreate(PhotoShareBase):
    pass

class AlbumShareCreate(AlbumShareBase):
    pass

class PhotoCommentCreate(PhotoCommentBase):
    pass

class PhotoReactionCreate(PhotoReactionBase):
    pass

# Update schemas
class PhotoUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_favorite: Optional[bool] = None
    is_private: Optional[bool] = None

class PhotoAlbumUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    cover_photo_id: Optional[int] = None
    is_private: Optional[bool] = None

# Response schemas
class PhotoTag(PhotoTagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PhotoShare(PhotoShareBase):
    id: int
    photo_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AlbumShare(AlbumShareBase):
    id: int
    album_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PhotoComment(PhotoCommentBase):
    id: int
    photo_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PhotoReaction(PhotoReactionBase):
    id: int
    photo_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PhotoAlbum(PhotoAlbumBase):
    id: int
    owner_id: int
    cover_photo_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    photo_count: Optional[int] = None

    class Config:
        from_attributes = True

class Photo(PhotoBase):
    id: int
    owner_id: int
    file_path: str
    thumbnail_path: str
    view_count: int
    created_at: datetime
    updated_at: datetime
    tags: List[PhotoTag] = []
    comment_count: Optional[int] = None
    reaction_count: Optional[int] = None

    class Config:
        from_attributes = True

class PhotoWithDetails(Photo):
    comments: List[PhotoComment] = []
    reactions: List[PhotoReaction] = []
    shares: List[PhotoShare] = []
    albums: List[PhotoAlbum] = []

    class Config:
        from_attributes = True

class PhotoStats(BaseModel):
    total_photos: int
    total_size: int  # in bytes
    by_month: Dict[str, int]  # YYYY-MM: count
    by_type: Dict[str, int]  # file_type: count
    favorite_count: int
    shared_count: int
    total_albums: int
    total_tags: int
    most_used_tags: List[Dict[str, int]]  # [{"name": tag_name, "count": count}]

class PhotoUploadResponse(BaseModel):
    id: int
    upload_url: str
    thumbnail_upload_url: str
    expires_at: datetime 