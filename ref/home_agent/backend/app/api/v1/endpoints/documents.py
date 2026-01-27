from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ....core.database import get_db
from ....core.security import get_current_user
from ....models.user import User
from ....models.documents import Document, DocumentShare, DocumentVersion, DocumentFolder
from ....schemas.documents import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentShareCreate,
    DocumentVersionCreate,
    FolderCreate,
    FolderResponse
)
from ....services.documents import DocumentService

router = APIRouter()

@router.post("/", response_model=DocumentResponse)
async def create_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    folder_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new document."""
    service = DocumentService(db)
    return await service.create_document(
        user_id=current_user.id,
        title=title,
        file=file,
        folder_id=folder_id
    )

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents accessible to the user."""
    service = DocumentService(db)
    return await service.list_documents(current_user.id)

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific document."""
    service = DocumentService(db)
    return await service.get_document(document_id, current_user.id)

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a document."""
    service = DocumentService(db)
    return await service.update_document(
        document_id=document_id,
        user_id=current_user.id,
        update_data=update_data
    )

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document."""
    service = DocumentService(db)
    return await service.delete_document(document_id, current_user.id)

@router.post("/{document_id}/versions", response_model=DocumentResponse)
async def create_version(
    document_id: int,
    file: UploadFile = File(...),
    changes_summary: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new version of a document."""
    service = DocumentService(db)
    return await service.create_version(
        document_id=document_id,
        user_id=current_user.id,
        file=file,
        changes_summary=changes_summary
    )

@router.get("/{document_id}/versions", response_model=List[DocumentResponse])
async def list_versions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all versions of a document."""
    service = DocumentService(db)
    return await service.list_versions(document_id, current_user.id)

@router.post("/{document_id}/share")
async def share_document(
    document_id: int,
    share_data: DocumentShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share a document with another user."""
    service = DocumentService(db)
    return await service.share_document(
        document_id=document_id,
        user_id=current_user.id,
        share_data=share_data
    )

@router.post("/folders", response_model=FolderResponse)
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new folder."""
    service = DocumentService(db)
    return await service.create_folder(
        user_id=current_user.id,
        folder_data=folder_data
    )

@router.get("/folders/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific folder."""
    service = DocumentService(db)
    return await service.get_folder(folder_id, current_user.id)

@router.get("/search", response_model=List[DocumentResponse])
async def search_documents(
    query: str,
    tags: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search documents."""
    service = DocumentService(db)
    return await service.search_documents(
        user_id=current_user.id,
        query=query,
        tags=tags
    ) 