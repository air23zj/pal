from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import uuid
import os
from fastapi import HTTPException
import boto3
from PIL import Image
import io

from ..models.photo import (
    Photo,
    PhotoAlbum,
    PhotoTag,
    PhotoShare,
    AlbumShare,
    PhotoComment,
    PhotoReaction,
    photo_tag_association
)
from ..schemas.photo import (
    PhotoCreate,
    PhotoUpdate,
    PhotoAlbumCreate,
    PhotoAlbumUpdate,
    PhotoTagCreate,
    PhotoShareCreate,
    AlbumShareCreate,
    PhotoCommentCreate,
    PhotoReactionCreate,
    PhotoStats,
    PhotoUploadResponse
)
from ..core.config import settings

class PhotoService:
    THUMBNAIL_SIZE = (300, 300)
    ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]

    @staticmethod
    def get_s3_client():
        """Get AWS S3 client"""
        return boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

    @staticmethod
    def generate_file_path(user_id: int, file_type: str) -> Tuple[str, str]:
        """Generate unique file paths for original and thumbnail"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        extension = file_type.split('/')[-1]
        
        original_path = f"photos/{user_id}/{timestamp}_{unique_id}.{extension}"
        thumbnail_path = f"photos/{user_id}/thumbnails/{timestamp}_{unique_id}_thumb.{extension}"
        
        return original_path, thumbnail_path

    @staticmethod
    def generate_presigned_url(
        file_path: str, expires_in: int = 3600, operation: str = 'put_object'
    ) -> Tuple[str, datetime]:
        """Generate a presigned URL for S3 operations"""
        s3_client = PhotoService.get_s3_client()
        try:
            url = s3_client.generate_presigned_url(
                ClientMethod=operation,
                Params={
                    'Bucket': settings.S3_BUCKET_NAME,
                    'Key': file_path
                },
                ExpiresIn=expires_in
            )
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            return url, expires_at
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )

    @staticmethod
    def create_photo(
        db: Session, user_id: int, photo: PhotoCreate
    ) -> Photo:
        """Create a new photo record"""
        if photo.file_type not in PhotoService.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type {photo.file_type} not allowed"
            )

        file_path, thumbnail_path = PhotoService.generate_file_path(
            user_id, photo.file_type
        )

        db_photo = Photo(
            **photo.model_dump(),
            owner_id=user_id,
            file_path=file_path,
            thumbnail_path=thumbnail_path
        )
        db.add(db_photo)
        db.commit()
        db.refresh(db_photo)
        return db_photo

    @staticmethod
    def get_photos(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        album_id: Optional[int] = None,
        tag_name: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        search: Optional[str] = None,
        shared_only: bool = False
    ) -> List[Photo]:
        """Get photos with various filters"""
        query = db.query(Photo)

        if shared_only:
            query = query.join(PhotoShare)\
                .filter(PhotoShare.shared_with_id == user_id)
        else:
            query = query.filter(Photo.owner_id == user_id)

        if album_id:
            query = query.join(Photo.albums)\
                .filter(PhotoAlbum.id == album_id)

        if tag_name:
            query = query.join(Photo.tags)\
                .filter(PhotoTag.name == tag_name)

        if is_favorite is not None:
            query = query.filter(Photo.is_favorite == is_favorite)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Photo.title.ilike(search_term),
                    Photo.description.ilike(search_term),
                    Photo.location.ilike(search_term)
                )
            )

        return query.order_by(desc(Photo.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_photo(
        db: Session, user_id: int, photo_id: int
    ) -> Optional[Photo]:
        """Get a specific photo"""
        photo = db.query(Photo)\
            .filter(
                Photo.id == photo_id,
                or_(
                    Photo.owner_id == user_id,
                    and_(
                        Photo.is_private == False,
                        db.query(PhotoShare)
                        .filter(
                            PhotoShare.photo_id == photo_id,
                            PhotoShare.shared_with_id == user_id
                        ).exists()
                    )
                )
            )\
            .first()

        if photo:
            photo.view_count += 1
            db.commit()

        return photo

    @staticmethod
    def update_photo(
        db: Session, user_id: int, photo_id: int, photo: PhotoUpdate
    ) -> Optional[Photo]:
        """Update a photo"""
        db_photo = db.query(Photo)\
            .filter(
                Photo.id == photo_id,
                Photo.owner_id == user_id
            )\
            .first()

        if not db_photo:
            return None

        update_data = photo.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_photo, field, value)

        db.commit()
        db.refresh(db_photo)
        return db_photo

    @staticmethod
    def delete_photo(
        db: Session, user_id: int, photo_id: int
    ) -> bool:
        """Delete a photo"""
        db_photo = db.query(Photo)\
            .filter(
                Photo.id == photo_id,
                Photo.owner_id == user_id
            )\
            .first()

        if db_photo:
            # Delete from S3
            try:
                s3_client = PhotoService.get_s3_client()
                s3_client.delete_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=db_photo.file_path
                )
                s3_client.delete_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=db_photo.thumbnail_path
                )
            except Exception:
                # Log error but continue with database deletion
                pass

            db.delete(db_photo)
            db.commit()
            return True
        return False

    @staticmethod
    def create_album(
        db: Session, user_id: int, album: PhotoAlbumCreate
    ) -> PhotoAlbum:
        """Create a new photo album"""
        db_album = PhotoAlbum(
            **album.model_dump(),
            owner_id=user_id
        )
        db.add(db_album)
        db.commit()
        db.refresh(db_album)
        return db_album

    @staticmethod
    def get_albums(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        shared_only: bool = False
    ) -> List[PhotoAlbum]:
        """Get photo albums"""
        query = db.query(PhotoAlbum)

        if shared_only:
            query = query.join(AlbumShare)\
                .filter(AlbumShare.shared_with_id == user_id)
        else:
            query = query.filter(PhotoAlbum.owner_id == user_id)

        return query.order_by(desc(PhotoAlbum.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def update_album(
        db: Session, user_id: int, album_id: int, album: PhotoAlbumUpdate
    ) -> Optional[PhotoAlbum]:
        """Update a photo album"""
        db_album = db.query(PhotoAlbum)\
            .filter(
                PhotoAlbum.id == album_id,
                PhotoAlbum.owner_id == user_id
            )\
            .first()

        if not db_album:
            return None

        update_data = album.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_album, field, value)

        db.commit()
        db.refresh(db_album)
        return db_album

    @staticmethod
    def delete_album(
        db: Session, user_id: int, album_id: int
    ) -> bool:
        """Delete a photo album"""
        db_album = db.query(PhotoAlbum)\
            .filter(
                PhotoAlbum.id == album_id,
                PhotoAlbum.owner_id == user_id
            )\
            .first()

        if db_album:
            db.delete(db_album)
            db.commit()
            return True
        return False

    @staticmethod
    def add_photos_to_album(
        db: Session, user_id: int, album_id: int, photo_ids: List[int]
    ) -> PhotoAlbum:
        """Add photos to an album"""
        db_album = db.query(PhotoAlbum)\
            .filter(
                PhotoAlbum.id == album_id,
                PhotoAlbum.owner_id == user_id
            )\
            .first()

        if not db_album:
            raise HTTPException(status_code=404, detail="Album not found")

        photos = db.query(Photo)\
            .filter(
                Photo.id.in_(photo_ids),
                Photo.owner_id == user_id
            )\
            .all()

        db_album.photos.extend(photos)
        db.commit()
        db.refresh(db_album)
        return db_album

    @staticmethod
    def remove_photos_from_album(
        db: Session, user_id: int, album_id: int, photo_ids: List[int]
    ) -> PhotoAlbum:
        """Remove photos from an album"""
        db_album = db.query(PhotoAlbum)\
            .filter(
                PhotoAlbum.id == album_id,
                PhotoAlbum.owner_id == user_id
            )\
            .first()

        if not db_album:
            raise HTTPException(status_code=404, detail="Album not found")

        photos = db.query(Photo)\
            .filter(Photo.id.in_(photo_ids))\
            .all()

        for photo in photos:
            db_album.photos.remove(photo)

        db.commit()
        db.refresh(db_album)
        return db_album

    @staticmethod
    def share_photo(
        db: Session, user_id: int, photo_id: int, share: PhotoShareCreate
    ) -> PhotoShare:
        """Share a photo with another user"""
        db_photo = db.query(Photo)\
            .filter(
                Photo.id == photo_id,
                Photo.owner_id == user_id
            )\
            .first()

        if not db_photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        existing_share = db.query(PhotoShare)\
            .filter(
                PhotoShare.photo_id == photo_id,
                PhotoShare.shared_with_id == share.shared_with_id
            )\
            .first()

        if existing_share:
            raise HTTPException(
                status_code=400,
                detail="Photo already shared with this user"
            )

        db_share = PhotoShare(
            photo_id=photo_id,
            **share.model_dump()
        )
        db.add(db_share)
        db.commit()
        db.refresh(db_share)
        return db_share

    @staticmethod
    def share_album(
        db: Session, user_id: int, album_id: int, share: AlbumShareCreate
    ) -> AlbumShare:
        """Share an album with another user"""
        db_album = db.query(PhotoAlbum)\
            .filter(
                PhotoAlbum.id == album_id,
                PhotoAlbum.owner_id == user_id
            )\
            .first()

        if not db_album:
            raise HTTPException(status_code=404, detail="Album not found")

        existing_share = db.query(AlbumShare)\
            .filter(
                AlbumShare.album_id == album_id,
                AlbumShare.shared_with_id == share.shared_with_id
            )\
            .first()

        if existing_share:
            raise HTTPException(
                status_code=400,
                detail="Album already shared with this user"
            )

        db_share = AlbumShare(
            album_id=album_id,
            **share.model_dump()
        )
        db.add(db_share)
        db.commit()
        db.refresh(db_share)
        return db_share

    @staticmethod
    def add_comment(
        db: Session, user_id: int, photo_id: int, comment: PhotoCommentCreate
    ) -> PhotoComment:
        """Add a comment to a photo"""
        db_photo = PhotoService.get_photo(db, user_id, photo_id)
        if not db_photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        db_comment = PhotoComment(
            photo_id=photo_id,
            author_id=user_id,
            **comment.model_dump()
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment

    @staticmethod
    def add_reaction(
        db: Session, user_id: int, photo_id: int, reaction: PhotoReactionCreate
    ) -> PhotoReaction:
        """Add a reaction to a photo"""
        db_photo = PhotoService.get_photo(db, user_id, photo_id)
        if not db_photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        existing_reaction = db.query(PhotoReaction)\
            .filter(
                PhotoReaction.photo_id == photo_id,
                PhotoReaction.user_id == user_id
            )\
            .first()

        if existing_reaction:
            existing_reaction.reaction = reaction.reaction
            db.commit()
            db.refresh(existing_reaction)
            return existing_reaction

        db_reaction = PhotoReaction(
            photo_id=photo_id,
            user_id=user_id,
            **reaction.model_dump()
        )
        db.add(db_reaction)
        db.commit()
        db.refresh(db_reaction)
        return db_reaction

    @staticmethod
    def get_photo_stats(
        db: Session, user_id: int
    ) -> PhotoStats:
        """Get statistics about user's photos"""
        # Get basic counts
        total_photos = db.query(func.count(Photo.id))\
            .filter(Photo.owner_id == user_id)\
            .scalar()

        total_size = db.query(func.sum(Photo.file_size))\
            .filter(Photo.owner_id == user_id)\
            .scalar() or 0

        # Get counts by month
        month_counts = {}
        results = db.query(
            func.date_trunc('month', Photo.created_at).label('month'),
            func.count(Photo.id)
        )\
            .filter(Photo.owner_id == user_id)\
            .group_by('month')\
            .all()
        for month, count in results:
            month_key = month.strftime("%Y-%m")
            month_counts[month_key] = count

        # Get counts by file type
        type_counts = {}
        results = db.query(
            Photo.file_type,
            func.count(Photo.id)
        )\
            .filter(Photo.owner_id == user_id)\
            .group_by(Photo.file_type)\
            .all()
        for file_type, count in results:
            type_counts[file_type] = count

        # Get other counts
        favorite_count = db.query(func.count(Photo.id))\
            .filter(
                Photo.owner_id == user_id,
                Photo.is_favorite == True
            )\
            .scalar()

        shared_count = db.query(func.count(Photo.id))\
            .join(PhotoShare)\
            .filter(Photo.owner_id == user_id)\
            .distinct()\
            .scalar()

        total_albums = db.query(func.count(PhotoAlbum.id))\
            .filter(PhotoAlbum.owner_id == user_id)\
            .scalar()

        # Get tag statistics
        total_tags = db.query(func.count(PhotoTag.id))\
            .join(photo_tag_association)\
            .join(Photo)\
            .filter(Photo.owner_id == user_id)\
            .distinct()\
            .scalar()

        most_used_tags = db.query(
            PhotoTag.name,
            func.count(photo_tag_association.c.photo_id).label('count')
        )\
            .join(photo_tag_association)\
            .join(Photo)\
            .filter(Photo.owner_id == user_id)\
            .group_by(PhotoTag.name)\
            .order_by(desc('count'))\
            .limit(10)\
            .all()

        return PhotoStats(
            total_photos=total_photos,
            total_size=total_size,
            by_month=month_counts,
            by_type=type_counts,
            favorite_count=favorite_count,
            shared_count=shared_count,
            total_albums=total_albums,
            total_tags=total_tags,
            most_used_tags=[
                {"name": name, "count": count}
                for name, count in most_used_tags
            ]
        )

    @staticmethod
    def initiate_upload(
        db: Session, user_id: int, photo: PhotoCreate
    ) -> PhotoUploadResponse:
        """Initiate a photo upload by creating the record and generating upload URLs"""
        db_photo = PhotoService.create_photo(db, user_id, photo)
        
        upload_url, expires_at = PhotoService.generate_presigned_url(
            db_photo.file_path
        )
        thumbnail_upload_url, _ = PhotoService.generate_presigned_url(
            db_photo.thumbnail_path
        )

        return PhotoUploadResponse(
            id=db_photo.id,
            upload_url=upload_url,
            thumbnail_upload_url=thumbnail_upload_url,
            expires_at=expires_at
        ) 