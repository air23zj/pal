from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import uuid
import os
from fastapi import HTTPException
import boto3
import mimetypes

from ..models.document import (
    Document,
    DocumentVersion,
    DocumentFolder,
    DocumentTag,
    DocumentShare,
    DocumentFolderShare,
    DocumentComment,
    document_tag_association,
    DocumentType
)
from ..schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentFolderCreate,
    DocumentFolderUpdate,
    DocumentTagCreate,
    DocumentShareCreate,
    DocumentFolderShareCreate,
    DocumentCommentCreate,
    DocumentVersionCreate,
    DocumentStats,
    DocumentUploadResponse
)
from ..core.config import settings

class DocumentService:
    ALLOWED_MIME_TYPES = {
        "text/plain": DocumentType.TEXT,
        "application/pdf": DocumentType.PDF,
        "application/msword": DocumentType.WORD,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.WORD,
        "application/vnd.ms-excel": DocumentType.EXCEL,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DocumentType.EXCEL,
        "application/vnd.ms-powerpoint": DocumentType.POWERPOINT,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": DocumentType.POWERPOINT,
        "image/jpeg": DocumentType.IMAGE,
        "image/png": DocumentType.IMAGE,
        "image/gif": DocumentType.IMAGE,
        "image/webp": DocumentType.IMAGE
    }

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
    def generate_file_path(user_id: int, filename: str) -> str:
        """Generate a unique file path for the document"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        extension = os.path.splitext(filename)[1]
        return f"documents/{user_id}/{timestamp}_{unique_id}{extension}"

    @staticmethod
    def generate_presigned_url(
        file_path: str, expires_in: int = 3600, operation: str = 'put_object'
    ) -> Tuple[str, datetime]:
        """Generate a presigned URL for S3 operations"""
        s3_client = DocumentService.get_s3_client()
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
    def get_document_type(mime_type: str) -> DocumentType:
        """Get document type from MIME type"""
        return DocumentService.ALLOWED_MIME_TYPES.get(mime_type, DocumentType.OTHER)

    @staticmethod
    def create_document(
        db: Session, user_id: int, document: DocumentCreate
    ) -> Document:
        """Create a new document record"""
        if document.mime_type not in DocumentService.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type {document.mime_type} not allowed"
            )

        file_path = DocumentService.generate_file_path(
            user_id, document.original_filename
        )

        db_document = Document(
            **document.model_dump(),
            owner_id=user_id,
            file_path=file_path
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document

    @staticmethod
    def get_documents(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        folder_id: Optional[int] = None,
        tag_name: Optional[str] = None,
        file_type: Optional[DocumentType] = None,
        is_favorite: Optional[bool] = None,
        is_archived: Optional[bool] = None,
        search: Optional[str] = None,
        shared_only: bool = False
    ) -> List[Document]:
        """Get documents with various filters"""
        query = db.query(Document)

        if shared_only:
            query = query.join(DocumentShare)\
                .filter(DocumentShare.shared_with_id == user_id)
        else:
            query = query.filter(Document.owner_id == user_id)

        if folder_id is not None:
            query = query.filter(Document.folder_id == folder_id)

        if tag_name:
            query = query.join(Document.tags)\
                .filter(DocumentTag.name == tag_name)

        if file_type:
            query = query.filter(Document.file_type == file_type)

        if is_favorite is not None:
            query = query.filter(Document.is_favorite == is_favorite)

        if is_archived is not None:
            query = query.filter(Document.is_archived == is_archived)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Document.title.ilike(search_term),
                    Document.description.ilike(search_term),
                    Document.original_filename.ilike(search_term)
                )
            )

        return query.order_by(desc(Document.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_document(
        db: Session, user_id: int, document_id: int
    ) -> Optional[Document]:
        """Get a specific document"""
        document = db.query(Document)\
            .filter(
                Document.id == document_id,
                or_(
                    Document.owner_id == user_id,
                    and_(
                        Document.is_private == False,
                        db.query(DocumentShare)
                        .filter(
                            DocumentShare.document_id == document_id,
                            DocumentShare.shared_with_id == user_id
                        ).exists()
                    )
                )
            )\
            .first()

        if document:
            document.view_count += 1
            db.commit()

        return document

    @staticmethod
    def update_document(
        db: Session, user_id: int, document_id: int, document: DocumentUpdate
    ) -> Optional[Document]:
        """Update a document"""
        db_document = db.query(Document)\
            .filter(
                Document.id == document_id,
                Document.owner_id == user_id
            )\
            .first()

        if not db_document:
            return None

        update_data = document.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_document, field, value)

        db.commit()
        db.refresh(db_document)
        return db_document

    @staticmethod
    def delete_document(
        db: Session, user_id: int, document_id: int
    ) -> bool:
        """Delete a document"""
        db_document = db.query(Document)\
            .filter(
                Document.id == document_id,
                Document.owner_id == user_id
            )\
            .first()

        if db_document:
            # Delete from S3
            try:
                s3_client = DocumentService.get_s3_client()
                # Delete main document
                s3_client.delete_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=db_document.file_path
                )
                # Delete versions
                for version in db_document.versions:
                    s3_client.delete_object(
                        Bucket=settings.S3_BUCKET_NAME,
                        Key=version.file_path
                    )
            except Exception:
                # Log error but continue with database deletion
                pass

            db.delete(db_document)
            db.commit()
            return True
        return False

    @staticmethod
    def create_folder(
        db: Session, user_id: int, folder: DocumentFolderCreate
    ) -> DocumentFolder:
        """Create a new document folder"""
        if folder.parent_id:
            parent = db.query(DocumentFolder)\
                .filter(
                    DocumentFolder.id == folder.parent_id,
                    DocumentFolder.owner_id == user_id
                )\
                .first()
            if not parent:
                raise HTTPException(
                    status_code=404,
                    detail="Parent folder not found"
                )

        db_folder = DocumentFolder(
            **folder.model_dump(),
            owner_id=user_id
        )
        db.add(db_folder)
        db.commit()
        db.refresh(db_folder)
        return db_folder

    @staticmethod
    def get_folders(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[int] = None,
        shared_only: bool = False
    ) -> List[DocumentFolder]:
        """Get document folders"""
        query = db.query(DocumentFolder)

        if shared_only:
            query = query.join(DocumentFolderShare)\
                .filter(DocumentFolderShare.shared_with_id == user_id)
        else:
            query = query.filter(DocumentFolder.owner_id == user_id)

        if parent_id is not None:
            query = query.filter(DocumentFolder.parent_id == parent_id)

        return query.order_by(DocumentFolder.name)\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def update_folder(
        db: Session, user_id: int, folder_id: int, folder: DocumentFolderUpdate
    ) -> Optional[DocumentFolder]:
        """Update a document folder"""
        db_folder = db.query(DocumentFolder)\
            .filter(
                DocumentFolder.id == folder_id,
                DocumentFolder.owner_id == user_id
            )\
            .first()

        if not db_folder:
            return None

        if folder.parent_id and folder.parent_id != db_folder.parent_id:
            parent = db.query(DocumentFolder)\
                .filter(
                    DocumentFolder.id == folder.parent_id,
                    DocumentFolder.owner_id == user_id
                )\
                .first()
            if not parent:
                raise HTTPException(
                    status_code=404,
                    detail="Parent folder not found"
                )

        update_data = folder.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_folder, field, value)

        db.commit()
        db.refresh(db_folder)
        return db_folder

    @staticmethod
    def delete_folder(
        db: Session, user_id: int, folder_id: int
    ) -> bool:
        """Delete a document folder"""
        db_folder = db.query(DocumentFolder)\
            .filter(
                DocumentFolder.id == folder_id,
                DocumentFolder.owner_id == user_id
            )\
            .first()

        if db_folder:
            db.delete(db_folder)
            db.commit()
            return True
        return False

    @staticmethod
    def create_version(
        db: Session,
        user_id: int,
        document_id: int,
        version: DocumentVersionCreate
    ) -> DocumentVersion:
        """Create a new document version"""
        db_document = DocumentService.get_document(db, user_id, document_id)
        if not db_document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get next version number
        next_version = db.query(func.max(DocumentVersion.version_number))\
            .filter(DocumentVersion.document_id == document_id)\
            .scalar() or 0
        next_version += 1

        # Generate new file path
        file_path = DocumentService.generate_file_path(
            user_id, db_document.original_filename
        )

        db_version = DocumentVersion(
            document_id=document_id,
            version_number=next_version,
            file_path=file_path,
            created_by_id=user_id,
            **version.model_dump()
        )
        db.add(db_version)
        db.commit()
        db.refresh(db_version)
        return db_version

    @staticmethod
    def share_document(
        db: Session, user_id: int, document_id: int, share: DocumentShareCreate
    ) -> DocumentShare:
        """Share a document with another user"""
        db_document = db.query(Document)\
            .filter(
                Document.id == document_id,
                Document.owner_id == user_id
            )\
            .first()

        if not db_document:
            raise HTTPException(status_code=404, detail="Document not found")

        existing_share = db.query(DocumentShare)\
            .filter(
                DocumentShare.document_id == document_id,
                DocumentShare.shared_with_id == share.shared_with_id
            )\
            .first()

        if existing_share:
            raise HTTPException(
                status_code=400,
                detail="Document already shared with this user"
            )

        db_share = DocumentShare(
            document_id=document_id,
            **share.model_dump()
        )
        db.add(db_share)
        db.commit()
        db.refresh(db_share)
        return db_share

    @staticmethod
    def share_folder(
        db: Session, user_id: int, folder_id: int, share: DocumentFolderShareCreate
    ) -> DocumentFolderShare:
        """Share a folder with another user"""
        db_folder = db.query(DocumentFolder)\
            .filter(
                DocumentFolder.id == folder_id,
                DocumentFolder.owner_id == user_id
            )\
            .first()

        if not db_folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        existing_share = db.query(DocumentFolderShare)\
            .filter(
                DocumentFolderShare.folder_id == folder_id,
                DocumentFolderShare.shared_with_id == share.shared_with_id
            )\
            .first()

        if existing_share:
            raise HTTPException(
                status_code=400,
                detail="Folder already shared with this user"
            )

        db_share = DocumentFolderShare(
            folder_id=folder_id,
            **share.model_dump()
        )
        db.add(db_share)
        db.commit()
        db.refresh(db_share)
        return db_share

    @staticmethod
    def add_comment(
        db: Session, user_id: int, document_id: int, comment: DocumentCommentCreate
    ) -> DocumentComment:
        """Add a comment to a document"""
        db_document = DocumentService.get_document(db, user_id, document_id)
        if not db_document:
            raise HTTPException(status_code=404, detail="Document not found")

        db_comment = DocumentComment(
            document_id=document_id,
            author_id=user_id,
            **comment.model_dump()
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment

    @staticmethod
    def get_document_stats(
        db: Session, user_id: int
    ) -> DocumentStats:
        """Get statistics about user's documents"""
        # Get basic counts
        total_documents = db.query(func.count(Document.id))\
            .filter(Document.owner_id == user_id)\
            .scalar()

        total_size = db.query(func.sum(Document.file_size))\
            .filter(Document.owner_id == user_id)\
            .scalar() or 0

        # Get counts by type
        type_counts = {}
        results = db.query(
            Document.file_type,
            func.count(Document.id)
        )\
            .filter(Document.owner_id == user_id)\
            .group_by(Document.file_type)\
            .all()
        for file_type, count in results:
            type_counts[file_type.value] = count

        # Get counts by month
        month_counts = {}
        results = db.query(
            func.date_trunc('month', Document.created_at).label('month'),
            func.count(Document.id)
        )\
            .filter(Document.owner_id == user_id)\
            .group_by('month')\
            .all()
        for month, count in results:
            month_key = month.strftime("%Y-%m")
            month_counts[month_key] = count

        # Get other counts
        favorite_count = db.query(func.count(Document.id))\
            .filter(
                Document.owner_id == user_id,
                Document.is_favorite == True
            )\
            .scalar()

        archived_count = db.query(func.count(Document.id))\
            .filter(
                Document.owner_id == user_id,
                Document.is_archived == True
            )\
            .scalar()

        shared_count = db.query(func.count(Document.id))\
            .join(DocumentShare)\
            .filter(Document.owner_id == user_id)\
            .distinct()\
            .scalar()

        total_folders = db.query(func.count(DocumentFolder.id))\
            .filter(DocumentFolder.owner_id == user_id)\
            .scalar()

        # Get tag statistics
        total_tags = db.query(func.count(DocumentTag.id))\
            .join(document_tag_association)\
            .join(Document)\
            .filter(Document.owner_id == user_id)\
            .distinct()\
            .scalar()

        most_used_tags = db.query(
            DocumentTag.name,
            func.count(document_tag_association.c.document_id).label('count')
        )\
            .join(document_tag_association)\
            .join(Document)\
            .filter(Document.owner_id == user_id)\
            .group_by(DocumentTag.name)\
            .order_by(desc('count'))\
            .limit(10)\
            .all()

        return DocumentStats(
            total_documents=total_documents,
            total_size=total_size,
            by_type=type_counts,
            by_month=month_counts,
            favorite_count=favorite_count,
            archived_count=archived_count,
            shared_count=shared_count,
            total_folders=total_folders,
            total_tags=total_tags,
            most_used_tags=[
                {"name": name, "count": count}
                for name, count in most_used_tags
            ]
        )

    @staticmethod
    def initiate_upload(
        db: Session, user_id: int, document: DocumentCreate
    ) -> DocumentUploadResponse:
        """Initiate a document upload by creating the record and generating upload URL"""
        db_document = DocumentService.create_document(db, user_id, document)
        
        upload_url, expires_at = DocumentService.generate_presigned_url(
            db_document.file_path
        )

        return DocumentUploadResponse(
            id=db_document.id,
            upload_url=upload_url,
            expires_at=expires_at
        ) 