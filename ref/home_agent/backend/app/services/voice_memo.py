from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
from datetime import datetime, timedelta
import boto3
import os
from fastapi import HTTPException
from botocore.exceptions import ClientError

from ..models.voice_memo import VoiceMemo, VoiceMemoShare, VoiceMemoStatus, VoiceMemoCategory
from ..schemas.voice_memo import (
    VoiceMemoCreate,
    VoiceMemoUpdate,
    VoiceMemoShareCreate,
    VoiceMemoStats,
    VoiceMemoUploadResponse
)
from ..core.config import settings

class VoiceMemoService:
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
    def generate_presigned_url(
        file_path: str, expires_in: int = 3600, operation: str = 'put_object'
    ) -> tuple[str, datetime]:
        """Generate a presigned URL for S3 operations"""
        s3_client = VoiceMemoService.get_s3_client()
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
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )

    @staticmethod
    def create_voice_memo(
        db: Session, user_id: int, memo: VoiceMemoCreate
    ) -> VoiceMemo:
        """Create a new voice memo record"""
        # Generate a unique file path for S3
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = f"voice_memos/{user_id}/{timestamp}.{memo.file_format}"

        db_memo = VoiceMemo(
            **memo.model_dump(),
            owner_id=user_id,
            file_path=file_path
        )
        db.add(db_memo)
        db.commit()
        db.refresh(db_memo)
        return db_memo

    @staticmethod
    def get_voice_memos(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        category: Optional[VoiceMemoCategory] = None,
        is_favorite: Optional[bool] = None,
        search: Optional[str] = None,
        shared_only: bool = False
    ) -> List[VoiceMemo]:
        """Get voice memos with various filters"""
        query = db.query(VoiceMemo)

        if shared_only:
            query = query.join(VoiceMemoShare)\
                .filter(VoiceMemoShare.shared_with_id == user_id)
        else:
            query = query.filter(VoiceMemo.owner_id == user_id)

        if category:
            query = query.filter(VoiceMemo.category == category)
        if is_favorite is not None:
            query = query.filter(VoiceMemo.is_favorite == is_favorite)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (VoiceMemo.title.ilike(search_term)) |
                (VoiceMemo.description.ilike(search_term)) |
                (VoiceMemo.tags.ilike(search_term))
            )

        return query.order_by(desc(VoiceMemo.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_voice_memo(
        db: Session, user_id: int, memo_id: int
    ) -> Optional[VoiceMemo]:
        """Get a specific voice memo"""
        return db.query(VoiceMemo)\
            .filter(
                VoiceMemo.id == memo_id,
                (
                    (VoiceMemo.owner_id == user_id) |
                    db.query(VoiceMemoShare)
                    .filter(
                        VoiceMemoShare.voice_memo_id == memo_id,
                        VoiceMemoShare.shared_with_id == user_id
                    ).exists()
                )
            )\
            .first()

    @staticmethod
    def update_voice_memo(
        db: Session, user_id: int, memo_id: int, memo: VoiceMemoUpdate
    ) -> Optional[VoiceMemo]:
        """Update a voice memo"""
        db_memo = VoiceMemoService.get_voice_memo(db, user_id, memo_id)
        if not db_memo:
            return None

        # Check if user has edit permission
        if db_memo.owner_id != user_id:
            share = db.query(VoiceMemoShare)\
                .filter(
                    VoiceMemoShare.voice_memo_id == memo_id,
                    VoiceMemoShare.shared_with_id == user_id,
                    VoiceMemoShare.can_edit == True
                )\
                .first()
            if not share:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to edit this voice memo"
                )

        update_data = memo.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_memo, field, value)

        db.commit()
        db.refresh(db_memo)
        return db_memo

    @staticmethod
    def delete_voice_memo(
        db: Session, user_id: int, memo_id: int
    ) -> bool:
        """Delete a voice memo"""
        db_memo = db.query(VoiceMemo)\
            .filter(
                VoiceMemo.id == memo_id,
                VoiceMemo.owner_id == user_id
            )\
            .first()

        if db_memo:
            # Mark as deleted first (soft delete)
            db_memo.status = VoiceMemoStatus.DELETED
            db.commit()

            # Delete from S3
            try:
                s3_client = VoiceMemoService.get_s3_client()
                s3_client.delete_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=db_memo.file_path
                )
            except ClientError:
                # Log error but continue with database deletion
                pass

            # Delete from database
            db.delete(db_memo)
            db.commit()
            return True
        return False

    @staticmethod
    def share_voice_memo(
        db: Session, user_id: int, memo_id: int, share: VoiceMemoShareCreate
    ) -> VoiceMemoShare:
        """Share a voice memo with another user"""
        db_memo = db.query(VoiceMemo)\
            .filter(
                VoiceMemo.id == memo_id,
                VoiceMemo.owner_id == user_id
            )\
            .first()
        if not db_memo:
            raise HTTPException(status_code=404, detail="Voice memo not found")

        # Check if already shared
        existing_share = db.query(VoiceMemoShare)\
            .filter(
                VoiceMemoShare.voice_memo_id == memo_id,
                VoiceMemoShare.shared_with_id == share.shared_with_id
            )\
            .first()
        if existing_share:
            raise HTTPException(
                status_code=400,
                detail="Voice memo already shared with this user"
            )

        db_share = VoiceMemoShare(
            voice_memo_id=memo_id,
            **share.model_dump()
        )
        db.add(db_share)
        db.commit()
        db.refresh(db_share)
        return db_share

    @staticmethod
    def remove_share(
        db: Session, user_id: int, memo_id: int, shared_with_id: int
    ) -> bool:
        """Remove a share from a voice memo"""
        db_share = db.query(VoiceMemoShare)\
            .join(VoiceMemo)\
            .filter(
                VoiceMemo.id == memo_id,
                VoiceMemo.owner_id == user_id,
                VoiceMemoShare.shared_with_id == shared_with_id
            )\
            .first()

        if db_share:
            db.delete(db_share)
            db.commit()
            return True
        return False

    @staticmethod
    def get_voice_memo_stats(
        db: Session, user_id: int
    ) -> VoiceMemoStats:
        """Get statistics about user's voice memos"""
        # Get basic counts
        total_count = db.query(func.count(VoiceMemo.id))\
            .filter(VoiceMemo.owner_id == user_id)\
            .scalar()

        total_duration = db.query(func.sum(VoiceMemo.duration))\
            .filter(VoiceMemo.owner_id == user_id)\
            .scalar() or 0.0

        total_size = db.query(func.sum(VoiceMemo.file_size))\
            .filter(VoiceMemo.owner_id == user_id)\
            .scalar() or 0

        # Get counts by category
        category_counts = {}
        for category in VoiceMemoCategory:
            count = db.query(func.count(VoiceMemo.id))\
                .filter(
                    VoiceMemo.owner_id == user_id,
                    VoiceMemo.category == category
                )\
                .scalar()
            category_counts[category] = count

        # Get counts by month
        month_counts = {}
        results = db.query(
            func.date_trunc('month', VoiceMemo.created_at).label('month'),
            func.count(VoiceMemo.id)
        )\
            .filter(VoiceMemo.owner_id == user_id)\
            .group_by('month')\
            .all()
        for month, count in results:
            month_key = month.strftime("%Y-%m")
            month_counts[month_key] = count

        # Get other counts
        favorite_count = db.query(func.count(VoiceMemo.id))\
            .filter(
                VoiceMemo.owner_id == user_id,
                VoiceMemo.is_favorite == True
            )\
            .scalar()

        shared_count = db.query(func.count(VoiceMemo.id))\
            .join(VoiceMemoShare)\
            .filter(VoiceMemo.owner_id == user_id)\
            .distinct()\
            .scalar()

        transcribed_count = db.query(func.count(VoiceMemo.id))\
            .filter(
                VoiceMemo.owner_id == user_id,
                VoiceMemo.transcription.isnot(None)
            )\
            .scalar()

        return VoiceMemoStats(
            total_count=total_count,
            total_duration=total_duration,
            total_size=total_size,
            by_category=category_counts,
            by_month=month_counts,
            favorite_count=favorite_count,
            shared_count=shared_count,
            transcribed_count=transcribed_count
        )

    @staticmethod
    def initiate_upload(
        db: Session, user_id: int, memo: VoiceMemoCreate
    ) -> VoiceMemoUploadResponse:
        """Initiate a voice memo upload by creating the record and generating upload URL"""
        db_memo = VoiceMemoService.create_voice_memo(db, user_id, memo)
        upload_url, expires_at = VoiceMemoService.generate_presigned_url(
            db_memo.file_path
        )
        return VoiceMemoUploadResponse(
            id=db_memo.id,
            upload_url=upload_url,
            expires_at=expires_at
        )

    @staticmethod
    def get_download_url(
        db: Session, user_id: int, memo_id: int
    ) -> str:
        """Get a download URL for a voice memo"""
        db_memo = VoiceMemoService.get_voice_memo(db, user_id, memo_id)
        if not db_memo:
            raise HTTPException(status_code=404, detail="Voice memo not found")

        # Update last played timestamp
        db_memo.last_played_at = datetime.utcnow()
        db.commit()

        # Generate download URL
        url, _ = VoiceMemoService.generate_presigned_url(
            db_memo.file_path,
            operation='get_object'
        )
        return url 