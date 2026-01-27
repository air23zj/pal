from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from ....core.deps import get_db, get_current_user
from ....models.user import User
from ....schemas.photo import (
    PhotoCreate,
    PhotoUpdate,
    Photo,
    PhotoAlbumCreate,
    PhotoAlbumUpdate,
    PhotoAlbum,
    PhotoTagCreate,
    PhotoTag,
    PhotoShareCreate,
    PhotoShare,
    AlbumShareCreate,
    AlbumShare,
    PhotoCommentCreate,
    PhotoComment,
    PhotoReactionCreate,
    PhotoReaction,
    PhotoStats,
    PhotoUploadResponse
)
from ....services.photo import PhotoService

router = APIRouter()

@router.post("/", response_model=PhotoUploadResponse)
def create_photo(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    photo: PhotoCreate
) -> PhotoUploadResponse:
    """Create a new photo and get upload URLs"""
    return PhotoService.initiate_upload(db, current_user.id, photo)

@router.get("/", response_model=List[Photo])
def get_photos(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    album_id: Optional[int] = None,
    tag_name: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    search: Optional[str] = None,
    shared_only: bool = False
) -> List[Photo]:
    """Get photos with various filters"""
    return PhotoService.get_photos(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        album_id=album_id,
        tag_name=tag_name,
        is_favorite=is_favorite,
        search=search,
        shared_only=shared_only
    )

@router.get("/{photo_id}", response_model=Photo)
def get_photo(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    photo_id: int
) -> Photo:
    """Get a specific photo"""
    photo = PhotoService.get_photo(db, current_user.id, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo

@router.put("/{photo_id}", response_model=Photo)
def update_photo(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    photo_id: int,
    photo: PhotoUpdate
) -> Photo:
    """Update a photo"""
    updated_photo = PhotoService.update_photo(
        db, current_user.id, photo_id, photo
    )
    if not updated_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return updated_photo

@router.delete("/{photo_id}")
def delete_photo(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    photo_id: int
) -> dict:
    """Delete a photo"""
    if PhotoService.delete_photo(db, current_user.id, photo_id):
        return {"message": "Photo deleted successfully"}
    raise HTTPException(status_code=404, detail="Photo not found")

@router.post("/albums/", response_model=PhotoAlbum)
def create_album(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    album: PhotoAlbumCreate
) -> PhotoAlbum:
    """Create a new photo album"""
    return PhotoService.create_album(db, current_user.id, album)

@router.get("/albums/", response_model=List[PhotoAlbum])
def get_albums(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    shared_only: bool = False
) -> List[PhotoAlbum]:
    """Get photo albums"""
    return PhotoService.get_albums(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        shared_only=shared_only
    )

@router.put("/albums/{album_id}", response_model=PhotoAlbum)
def update_album(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    album_id: int,
    album: PhotoAlbumUpdate
) -> PhotoAlbum:
    """Update a photo album"""
    updated_album = PhotoService.update_album(
        db, current_user.id, album_id, album
    )
    if not updated_album:
        raise HTTPException(status_code=404, detail="Album not found")
    return updated_album

@router.delete("/albums/{album_id}")
def delete_album(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    album_id: int
) -> dict:
    """Delete a photo album"""
    if PhotoService.delete_album(db, current_user.id, album_id):
        return {"message": "Album deleted successfully"}
    raise HTTPException(status_code=404, detail="Album not found")

@router.post("/albums/{album_id}/photos", response_model=PhotoAlbum)
def add_photos_to_album(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    album_id: int,
    photo_ids: List[int] = Body(...)
) -> PhotoAlbum:
    """Add photos to an album"""
    return PhotoService.add_photos_to_album(
        db, current_user.id, album_id, photo_ids
    )

@router.delete("/albums/{album_id}/photos", response_model=PhotoAlbum)
def remove_photos_from_album(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    album_id: int,
    photo_ids: List[int] = Body(...)
) -> PhotoAlbum:
    """Remove photos from an album"""
    return PhotoService.remove_photos_from_album(
        db, current_user.id, album_id, photo_ids
    )

@router.post("/{photo_id}/share", response_model=PhotoShare)
def share_photo(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    photo_id: int,
    share: PhotoShareCreate
) -> PhotoShare:
    """Share a photo with another user"""
    return PhotoService.share_photo(db, current_user.id, photo_id, share)

@router.post("/albums/{album_id}/share", response_model=AlbumShare)
def share_album(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    album_id: int,
    share: AlbumShareCreate
) -> AlbumShare:
    """Share an album with another user"""
    return PhotoService.share_album(db, current_user.id, album_id, share)

@router.post("/{photo_id}/comments", response_model=PhotoComment)
def add_comment(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    photo_id: int,
    comment: PhotoCommentCreate
) -> PhotoComment:
    """Add a comment to a photo"""
    return PhotoService.add_comment(db, current_user.id, photo_id, comment)

@router.post("/{photo_id}/reactions", response_model=PhotoReaction)
def add_reaction(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    photo_id: int,
    reaction: PhotoReactionCreate
) -> PhotoReaction:
    """Add a reaction to a photo"""
    return PhotoService.add_reaction(db, current_user.id, photo_id, reaction)

@router.get("/stats", response_model=PhotoStats)
def get_photo_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PhotoStats:
    """Get statistics about user's photos"""
    return PhotoService.get_photo_stats(db, current_user.id) 