import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.documents import (
    Document,
    DocumentVersion,
    DocumentShare,
    DocumentTag,
    DocumentFolder
)
from app.services.documents import DocumentService

def test_create_document(db: Session, test_user: dict):
    """Test creating a document."""
    document = Document(
        user_id=1,
        title="Project Proposal",
        content="This is the project proposal content...",
        file_path="/storage/documents/proposal.docx",
        file_type="application/docx",
        file_size=1024 * 1024,  # 1MB
        version=1,
        metadata={
            "author": "John Doe",
            "last_modified": datetime.utcnow().isoformat(),
            "word_count": 2500,
            "page_count": 10
        }
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    assert document.id is not None
    assert document.title == "Project Proposal"
    assert document.file_size == 1024 * 1024
    assert document.metadata["word_count"] == 2500

def test_create_document_version(db: Session):
    """Test creating a document version."""
    version = DocumentVersion(
        document_id=1,
        version_number=2,
        content="Updated project proposal content...",
        file_path="/storage/documents/proposal_v2.docx",
        file_size=1024 * 1024,
        created_at=datetime.utcnow(),
        created_by=1,
        changes_summary="Updated executive summary and budget sections",
        metadata={
            "word_count": 2600,
            "page_count": 11,
            "changes": [
                {"type": "addition", "section": "Executive Summary"},
                {"type": "modification", "section": "Budget"}
            ]
        }
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    assert version.id is not None
    assert version.version_number == 2
    assert len(version.metadata["changes"]) == 2

def test_create_document_share(db: Session, test_user: dict):
    """Test creating a document share."""
    share = DocumentShare(
        document_id=1,
        shared_with=2,
        permission="edit",
        expires_at=datetime.utcnow(),
        shared_by=1,
        share_link="https://example.com/share/xyz789",
        is_public=False,
        password="secure123",
        metadata={
            "access_count": 0,
            "last_accessed": None,
            "notifications_enabled": True
        }
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    assert share.id is not None
    assert share.permission == "edit"
    assert share.is_public is False
    assert share.metadata["notifications_enabled"] is True

def test_create_document_tag(db: Session):
    """Test creating a document tag."""
    tag = DocumentTag(
        document_id=1,
        name="proposal",
        color="#FF0000",
        created_by=1,
        metadata={
            "category": "business",
            "importance": "high",
            "automated": False
        }
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)

    assert tag.id is not None
    assert tag.name == "proposal"
    assert tag.color == "#FF0000"
    assert tag.metadata["importance"] == "high"

def test_create_document_folder(db: Session, test_user: dict):
    """Test creating a document folder."""
    folder = DocumentFolder(
        user_id=1,
        name="Project Documents",
        description="All project-related documents",
        parent_folder_id=None,
        is_shared=False,
        metadata={
            "document_count": 0,
            "total_size": 0,
            "last_modified": datetime.utcnow().isoformat()
        }
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)

    assert folder.id is not None
    assert folder.name == "Project Documents"
    assert folder.is_shared is False
    assert folder.metadata["document_count"] == 0

def test_document_service_crud(db: Session, test_user: dict):
    """Test document service CRUD operations."""
    service = DocumentService(db)
    
    # Create document
    doc = service.create_document(
        user_id=1,
        title="Test Document",
        content="Test content",
        file_type="text/plain"
    )
    assert doc.title == "Test Document"

    # Get document
    retrieved = service.get_document(doc.id)
    assert retrieved.content == "Test content"

    # Update document
    updated = service.update_document(
        doc.id,
        title="Updated Document"
    )
    assert updated.title == "Updated Document"

    # Delete document
    deleted = service.delete_document(doc.id)
    assert deleted is True

def test_document_service_versions(db: Session, test_user: dict):
    """Test document service version operations."""
    service = DocumentService(db)

    # Create test document
    doc = service.create_document(
        user_id=1,
        title="Test Document",
        content="Version 1"
    )

    # Create new version
    version = service.create_version(
        document_id=doc.id,
        content="Version 2",
        changes_summary="Updated content"
    )
    assert version.version_number == 2

    # Get versions
    versions = service.get_versions(doc.id)
    assert len(versions) == 2

def test_document_service_sharing(db: Session, test_user: dict):
    """Test document service sharing operations."""
    service = DocumentService(db)

    # Create test document
    doc = service.create_document(
        user_id=1,
        title="Test Document",
        content="Test content"
    )

    # Share document
    share = service.share_document(
        document_id=doc.id,
        shared_with=2,
        permission="view"
    )
    assert share.permission == "view"

    # Get shared documents
    shared = service.get_shared_documents(user_id=2)
    assert len(shared) == 1

def test_document_service_folders(db: Session, test_user: dict):
    """Test document service folder operations."""
    service = DocumentService(db)

    # Create folder
    folder = service.create_folder(
        user_id=1,
        name="Test Folder"
    )
    assert folder.name == "Test Folder"

    # Create document in folder
    doc = service.create_document(
        user_id=1,
        title="Test Document",
        content="Test content",
        folder_id=folder.id
    )
    assert doc.folder_id == folder.id

    # Get folder contents
    contents = service.get_folder_contents(folder.id)
    assert len(contents["documents"]) == 1

def test_document_service_search(db: Session, test_user: dict):
    """Test document service search operations."""
    service = DocumentService(db)

    # Create test documents
    service.create_document(
        user_id=1,
        title="Project Plan",
        content="Project planning document",
        tags=["project", "planning"]
    )
    service.create_document(
        user_id=1,
        title="Meeting Notes",
        content="Team meeting notes",
        tags=["meeting", "notes"]
    )

    # Search documents
    results = service.search_documents(
        user_id=1,
        query="project",
        tags=["project"]
    )
    assert len(results) == 1
    assert results[0].title == "Project Plan" 