from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    Text,
    BigInteger,
    Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..db.base_class import Base

# Association tables
document_tag_association = Table(
    'document_tag_association',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('document_tags.id', ondelete='CASCADE'))
)

class DocumentType(str, enum.Enum):
    TEXT = "text"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    IMAGE = "image"
    OTHER = "other"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=False)
    file_type = Column(SQLEnum(DocumentType), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # in bytes
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    is_favorite = Column(Boolean, default=False)
    is_private = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    owner = relationship("User", back_populates="documents")
    
    folder_id = Column(Integer, ForeignKey('document_folders.id', ondelete='SET NULL'), nullable=True)
    folder = relationship("DocumentFolder", back_populates="documents")
    
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    shares = relationship("DocumentShare", back_populates="document", cascade="all, delete-orphan")
    comments = relationship("DocumentComment", back_populates="document", cascade="all, delete-orphan")
    tags = relationship(
        "DocumentTag",
        secondary=document_tag_association,
        back_populates="documents"
    )

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="versions")
    created_by = relationship("User")

class DocumentFolder(Base):
    __tablename__ = "document_folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('document_folders.id', ondelete='CASCADE'), nullable=True)
    is_private = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    owner = relationship("User", back_populates="document_folders")
    
    documents = relationship("Document", back_populates="folder")
    subfolders = relationship("DocumentFolder", backref="parent", remote_side=[id])
    shares = relationship("DocumentFolderShare", back_populates="folder", cascade="all, delete-orphan")

class DocumentTag(Base):
    __tablename__ = "document_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(7), nullable=True)  # Hex color code
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    owner = relationship("User", back_populates="document_tags")
    
    documents = relationship(
        "Document",
        secondary=document_tag_association,
        back_populates="tags"
    )

class DocumentShare(Base):
    __tablename__ = "document_shares"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    shared_with_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    can_edit = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="shares")
    shared_with = relationship("User")

class DocumentFolderShare(Base):
    __tablename__ = "document_folder_shares"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey('document_folders.id', ondelete='CASCADE'), nullable=False)
    shared_with_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    can_edit = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    folder = relationship("DocumentFolder", back_populates="shares")
    shared_with = relationship("User")

class DocumentComment(Base):
    __tablename__ = "document_comments"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    document = relationship("Document", back_populates="comments")
    author = relationship("User") 