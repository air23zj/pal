from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    Float,
    Text,
    Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..db.base_class import Base

# Association tables
photo_tag_association = Table(
    'photo_tag_association',
    Base.metadata,
    Column('photo_id', Integer, ForeignKey('photos.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('photo_tags.id', ondelete='CASCADE'))
)

photo_album_association = Table(
    'photo_album_association',
    Base.metadata,
    Column('photo_id', Integer, ForeignKey('photos.id', ondelete='CASCADE')),
    Column('album_id', Integer, ForeignKey('photo_albums.id', ondelete='CASCADE'))
)

class ReactionType(str, enum.Enum):
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=False)
    thumbnail_path = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_favorite = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    owner = relationship("User", back_populates="photos")
    
    albums = relationship(
        "PhotoAlbum",
        secondary=photo_album_association,
        back_populates="photos"
    )
    
    tags = relationship(
        "PhotoTag",
        secondary=photo_tag_association,
        back_populates="photos"
    )
    
    shares = relationship("PhotoShare", back_populates="photo", cascade="all, delete-orphan")
    comments = relationship("PhotoComment", back_populates="photo", cascade="all, delete-orphan")
    reactions = relationship("PhotoReaction", back_populates="photo", cascade="all, delete-orphan")

class PhotoAlbum(Base):
    __tablename__ = "photo_albums"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_photo_id = Column(Integer, ForeignKey('photos.id', ondelete='SET NULL'), nullable=True)
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    owner = relationship("User", back_populates="albums")
    
    photos = relationship(
        "Photo",
        secondary=photo_album_association,
        back_populates="albums"
    )
    
    shares = relationship("AlbumShare", back_populates="album", cascade="all, delete-orphan")

class PhotoTag(Base):
    __tablename__ = "photo_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    photos = relationship(
        "Photo",
        secondary=photo_tag_association,
        back_populates="tags"
    )

class PhotoShare(Base):
    __tablename__ = "photo_shares"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey('photos.id', ondelete='CASCADE'), nullable=False)
    shared_with_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    can_edit = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    photo = relationship("Photo", back_populates="shares")
    shared_with = relationship("User")

class AlbumShare(Base):
    __tablename__ = "album_shares"

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey('photo_albums.id', ondelete='CASCADE'), nullable=False)
    shared_with_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    can_edit = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    album = relationship("PhotoAlbum", back_populates="shares")
    shared_with = relationship("User")

class PhotoComment(Base):
    __tablename__ = "photo_comments"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey('photos.id', ondelete='CASCADE'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    photo = relationship("Photo", back_populates="comments")
    author = relationship("User")

class PhotoReaction(Base):
    __tablename__ = "photo_reactions"

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey('photos.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reaction = Column(SQLEnum(ReactionType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    photo = relationship("Photo", back_populates="reactions")
    user = relationship("User") 