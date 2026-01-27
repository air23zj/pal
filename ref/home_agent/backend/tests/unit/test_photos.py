import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.photos import (
    Photo,
    PhotoAlbum,
    PhotoTag,
    PhotoShare,
    PhotoMetadata
)
from app.services.photos import PhotoService

def test_create_photo(db: Session, test_user: dict):
    """Test creating a photo."""
    photo = Photo(
        user_id=1,
        title="Vacation Photo",
        file_path="/storage/photos/vacation.jpg",
        file_size=2048576,  # 2MB
        file_type="image/jpeg",
        taken_at=datetime.utcnow(),
        metadata={
            "device": "iPhone 13",
            "resolution": "4032x3024",
            "location": {
                "latitude": 37.7749,
                "longitude": -122.4194
            }
        }
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    assert photo.id is not None
    assert photo.title == "Vacation Photo"
    assert photo.file_size == 2048576
    assert photo.file_type == "image/jpeg"
    assert "resolution" in photo.metadata

def test_create_photo_album(db: Session, test_user: dict):
    """Test creating a photo album."""
    album = PhotoAlbum(
        user_id=1,
        name="Summer Vacation",
        description="Photos from summer vacation 2023",
        cover_photo_id=None,
        is_shared=False,
        metadata={
            "location": "San Francisco",
            "date_range": {
                "start": "2023-06-01",
                "end": "2023-06-15"
            }
        }
    )
    db.add(album)
    db.commit()
    db.refresh(album)

    assert album.id is not None
    assert album.name == "Summer Vacation"
    assert album.is_shared is False
    assert "location" in album.metadata

def test_create_photo_tag(db: Session):
    """Test creating a photo tag."""
    tag = PhotoTag(
        photo_id=1,
        name="beach",
        confidence=0.95,
        source="auto",
        metadata={
            "category": "landscape",
            "detected_objects": ["sand", "ocean", "sky"]
        }
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)

    assert tag.id is not None
    assert tag.name == "beach"
    assert tag.confidence == 0.95
    assert "category" in tag.metadata

def test_create_photo_share(db: Session, test_user: dict):
    """Test creating a photo share."""
    share = PhotoShare(
        photo_id=1,
        shared_with=2,
        permission="view",
        expires_at=datetime.utcnow(),
        shared_by=1,
        share_link="https://example.com/share/abc123",
        is_public=False
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    assert share.id is not None
    assert share.permission == "view"
    assert share.is_public is False
    assert share.share_link == "https://example.com/share/abc123"

def test_create_photo_metadata(db: Session):
    """Test creating photo metadata."""
    metadata = PhotoMetadata(
        photo_id=1,
        camera_make="Apple",
        camera_model="iPhone 13",
        lens_model="Wide",
        focal_length=26,
        aperture="f/1.6",
        iso=100,
        exposure_time="1/125",
        gps_latitude=37.7749,
        gps_longitude=-122.4194,
        altitude=10,
        color_space="sRGB"
    )
    db.add(metadata)
    db.commit()
    db.refresh(metadata)

    assert metadata.id is not None
    assert metadata.camera_make == "Apple"
    assert metadata.focal_length == 26
    assert metadata.gps_latitude == 37.7749

def test_photo_service_upload(db: Session, test_user: dict):
    """Test photo service upload operations."""
    service = PhotoService(db)
    
    # Upload photo
    photo = service.upload_photo(
        user_id=1,
        file_path="/storage/photos/test.jpg",
        title="Test Photo",
        metadata={
            "device": "iPhone 13",
            "resolution": "4032x3024"
        }
    )
    assert photo.title == "Test Photo"

    # Get photo
    retrieved = service.get_photo(photo.id)
    assert retrieved.file_path == "/storage/photos/test.jpg"

    # Update photo
    updated = service.update_photo(
        photo.id,
        title="Updated Title"
    )
    assert updated.title == "Updated Title"

    # Delete photo
    deleted = service.delete_photo(photo.id)
    assert deleted is True

def test_photo_service_albums(db: Session, test_user: dict):
    """Test photo service album operations."""
    service = PhotoService(db)

    # Create album
    album = service.create_album(
        user_id=1,
        name="Test Album",
        description="Test Description"
    )
    assert album.name == "Test Album"

    # Add photo to album
    photo = service.upload_photo(
        user_id=1,
        file_path="/storage/photos/test.jpg",
        title="Test Photo"
    )
    added = service.add_to_album(
        photo_id=photo.id,
        album_id=album.id
    )
    assert added is True

    # Get album photos
    photos = service.get_album_photos(album.id)
    assert len(photos) == 1

def test_photo_service_tags(db: Session, test_user: dict):
    """Test photo service tag operations."""
    service = PhotoService(db)

    # Upload test photo
    photo = service.upload_photo(
        user_id=1,
        file_path="/storage/photos/test.jpg",
        title="Test Photo"
    )

    # Add tags
    tags = service.add_tags(
        photo_id=photo.id,
        tags=["beach", "sunset"],
        source="manual"
    )
    assert len(tags) == 2
    assert any(t.name == "beach" for t in tags)

    # Get photo tags
    retrieved = service.get_photo_tags(photo.id)
    assert len(retrieved) == 2

def test_photo_service_sharing(db: Session, test_user: dict):
    """Test photo service sharing operations."""
    service = PhotoService(db)

    # Upload test photo
    photo = service.upload_photo(
        user_id=1,
        file_path="/storage/photos/test.jpg",
        title="Test Photo"
    )

    # Share photo
    share = service.share_photo(
        photo_id=photo.id,
        shared_with=2,
        permission="view"
    )
    assert share.permission == "view"

    # Get shared photos
    shared = service.get_shared_photos(user_id=2)
    assert len(shared) == 1

def test_photo_service_search(db: Session, test_user: dict):
    """Test photo service search operations."""
    service = PhotoService(db)

    # Upload test photos with tags
    photo1 = service.upload_photo(
        user_id=1,
        file_path="/storage/photos/beach.jpg",
        title="Beach Day"
    )
    service.add_tags(
        photo_id=photo1.id,
        tags=["beach", "summer"],
        source="manual"
    )

    photo2 = service.upload_photo(
        user_id=1,
        file_path="/storage/photos/mountain.jpg",
        title="Mountain Hike"
    )
    service.add_tags(
        photo_id=photo2.id,
        tags=["mountain", "hiking"],
        source="manual"
    )

    # Search photos
    results = service.search_photos(
        user_id=1,
        query="beach"
    )
    assert len(results) == 1
    assert results[0].title == "Beach Day"

def test_photo_service_metadata(db: Session, test_user: dict):
    """Test photo service metadata operations."""
    service = PhotoService(db)

    # Upload test photo
    photo = service.upload_photo(
        user_id=1,
        file_path="/storage/photos/test.jpg",
        title="Test Photo"
    )

    # Add metadata
    metadata = service.add_metadata(
        photo_id=photo.id,
        metadata={
            "camera_make": "Apple",
            "camera_model": "iPhone 13",
            "focal_length": 26
        }
    )
    assert metadata.camera_make == "Apple"

    # Get metadata
    retrieved = service.get_photo_metadata(photo.id)
    assert retrieved.focal_length == 26 