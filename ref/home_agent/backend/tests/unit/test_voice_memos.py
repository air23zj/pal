import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.voice_memos import (
    VoiceMemo,
    VoiceMemoTranscription,
    VoiceMemoTag,
    VoiceMemoShare,
    VoiceMemoFolder
)
from app.services.voice_memos import VoiceMemoService

def test_create_voice_memo(db: Session, test_user: dict):
    """Test creating a voice memo."""
    memo = VoiceMemo(
        user_id=1,
        title="Test Memo",
        duration=120,  # 2 minutes
        file_path="/storage/memos/test.webm",
        file_size=1024 * 1024,  # 1MB
        metadata={
            "device": "iPhone",
            "format": "webm",
            "sample_rate": 44100
        }
    )
    db.add(memo)
    db.commit()
    db.refresh(memo)

    assert memo.id is not None
    assert memo.title == "Test Memo"
    assert memo.duration == 120
    assert memo.file_size == 1024 * 1024

def test_create_transcription(db: Session):
    """Test creating a voice memo transcription."""
    transcription = VoiceMemoTranscription(
        memo_id=1,
        text="This is a test transcription",
        language="en",
        confidence=0.95,
        duration=120,
        segments=[
            {"start": 0, "end": 60, "text": "This is"},
            {"start": 61, "end": 120, "text": "a test transcription"}
        ]
    )
    db.add(transcription)
    db.commit()
    db.refresh(transcription)

    assert transcription.id is not None
    assert transcription.text == "This is a test transcription"
    assert transcription.confidence == 0.95
    assert len(transcription.segments) == 2

def test_create_memo_tag(db: Session, test_user: dict):
    """Test creating a voice memo tag."""
    tag = VoiceMemoTag(
        memo_id=1,
        name="important",
        color="#FF0000",
        created_by=1
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)

    assert tag.id is not None
    assert tag.name == "important"
    assert tag.color == "#FF0000"

def test_create_memo_share(db: Session, test_user: dict):
    """Test creating a voice memo share."""
    share = VoiceMemoShare(
        memo_id=1,
        shared_with=2,
        permission="view",
        expires_at=datetime.utcnow(),
        shared_by=1
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    assert share.id is not None
    assert share.permission == "view"
    assert share.shared_by == 1

def test_create_memo_folder(db: Session, test_user: dict):
    """Test creating a voice memo folder."""
    folder = VoiceMemoFolder(
        user_id=1,
        name="Test Folder",
        description="Test Description",
        parent_folder_id=None,
        is_shared=False
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)

    assert folder.id is not None
    assert folder.name == "Test Folder"
    assert folder.is_shared is False

def test_voice_memo_service_crud(db: Session, test_user: dict):
    """Test voice memo service CRUD operations."""
    service = VoiceMemoService(db)
    
    # Create memo
    memo = service.create_memo(
        user_id=1,
        title="Test Memo",
        file_path="/storage/memos/test.webm",
        duration=120
    )
    assert memo.title == "Test Memo"

    # Get memo
    retrieved = service.get_memo(memo.id)
    assert retrieved.duration == 120

    # Update memo
    updated = service.update_memo(
        memo.id,
        title="Updated Title"
    )
    assert updated.title == "Updated Title"

    # Delete memo
    deleted = service.delete_memo(memo.id)
    assert deleted is True

def test_voice_memo_service_transcription(db: Session, test_user: dict):
    """Test voice memo transcription functionality."""
    service = VoiceMemoService(db)

    # Create test memo
    memo = service.create_memo(
        user_id=1,
        title="Test Memo",
        file_path="/storage/memos/test.webm",
        duration=120
    )

    # Transcribe memo
    transcription = service.transcribe_memo(
        memo_id=memo.id,
        language="en"
    )
    assert transcription.language == "en"
    assert transcription.text is not None

    # Get transcription
    retrieved = service.get_transcription(memo.id)
    assert retrieved.confidence > 0

def test_voice_memo_service_sharing(db: Session, test_user: dict):
    """Test voice memo sharing functionality."""
    service = VoiceMemoService(db)

    # Create test memo
    memo = service.create_memo(
        user_id=1,
        title="Test Memo",
        file_path="/storage/memos/test.webm",
        duration=120
    )

    # Share memo
    share = service.share_memo(
        memo_id=memo.id,
        shared_with=2,
        permission="view"
    )
    assert share.permission == "view"

    # Get shared memos
    shared = service.get_shared_memos(user_id=2)
    assert len(shared) == 1

def test_voice_memo_service_folders(db: Session, test_user: dict):
    """Test voice memo folder functionality."""
    service = VoiceMemoService(db)

    # Create folder
    folder = service.create_folder(
        user_id=1,
        name="Test Folder"
    )
    assert folder.name == "Test Folder"

    # Create memo in folder
    memo = service.create_memo(
        user_id=1,
        title="Test Memo",
        file_path="/storage/memos/test.webm",
        duration=120,
        folder_id=folder.id
    )
    assert memo.folder_id == folder.id

    # Get folder contents
    contents = service.get_folder_contents(folder.id)
    assert len(contents["memos"]) == 1

def test_voice_memo_service_search(db: Session, test_user: dict):
    """Test voice memo search functionality."""
    service = VoiceMemoService(db)

    # Create test memos with transcriptions
    memo1 = service.create_memo(
        user_id=1,
        title="Meeting Notes",
        file_path="/storage/memos/meeting.webm",
        duration=120
    )
    service.create_transcription(
        memo_id=memo1.id,
        text="Discussion about project timeline"
    )

    memo2 = service.create_memo(
        user_id=1,
        title="Shopping List",
        file_path="/storage/memos/shopping.webm",
        duration=60
    )
    service.create_transcription(
        memo_id=memo2.id,
        text="Remember to buy groceries"
    )

    # Search memos
    results = service.search_memos(
        user_id=1,
        query="project timeline"
    )
    assert len(results) == 1
    assert results[0].title == "Meeting Notes" 