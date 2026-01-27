from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, constr
from enum import Enum

class DocumentType(str, Enum):
    TEXT = "text"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    IMAGE = "image"
    OTHER = "other"

# Base schemas
class DocumentBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    file_type: DocumentType
    file_size: int
    original_filename: str = Field(..., max_length=255)
    mime_type: str = Field(..., max_length=100)
    is_favorite: bool = False
    is_private: bool = True
    is_archived: bool = False

class DocumentFolderBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_private: bool = True

class DocumentTagBase(BaseModel):
    name: str = Field(..., max_length=50)
    color: Optional[str] = Field(None, max_length=7, regex="^#[0-9a-fA-F]{6}$")

class DocumentShareBase(BaseModel):
    shared_with_id: int
    can_edit: bool = False
    can_share: bool = False
    expires_at: Optional[datetime] = None

class DocumentFolderShareBase(BaseModel):
    shared_with_id: int
    can_edit: bool = False
    can_share: bool = False
    expires_at: Optional[datetime] = None

class DocumentCommentBase(BaseModel):
    content: str

class DocumentVersionBase(BaseModel):
    change_summary: Optional[str] = None

# Create schemas
class DocumentCreate(DocumentBase):
    folder_id: Optional[int] = None

class DocumentFolderCreate(DocumentFolderBase):
    pass

class DocumentTagCreate(DocumentTagBase):
    pass

class DocumentShareCreate(DocumentShareBase):
    pass

class DocumentFolderShareCreate(DocumentFolderShareBase):
    pass

class DocumentCommentCreate(DocumentCommentBase):
    pass

class DocumentVersionCreate(DocumentVersionBase):
    file_size: int

# Update schemas
class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    folder_id: Optional[int] = None
    is_favorite: Optional[bool] = None
    is_private: Optional[bool] = None
    is_archived: Optional[bool] = None

class DocumentFolderUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_private: Optional[bool] = None

class DocumentTagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=7, regex="^#[0-9a-fA-F]{6}$")

# Response schemas
class DocumentTag(DocumentTagBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentVersion(DocumentVersionBase):
    id: int
    document_id: int
    version_number: int
    file_path: str
    file_size: int
    created_at: datetime
    created_by_id: int

    class Config:
        from_attributes = True

class DocumentComment(DocumentCommentBase):
    id: int
    document_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentShare(DocumentShareBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentFolderShare(DocumentFolderShareBase):
    id: int
    folder_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentFolder(DocumentFolderBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = None
    subfolder_count: Optional[int] = None

    class Config:
        from_attributes = True

class Document(DocumentBase):
    id: int
    owner_id: int
    folder_id: Optional[int] = None
    file_path: str
    view_count: int
    created_at: datetime
    updated_at: datetime
    tags: List[DocumentTag] = []
    current_version: Optional[int] = None
    comment_count: Optional[int] = None
    version_count: Optional[int] = None

    class Config:
        from_attributes = True

class DocumentWithDetails(Document):
    versions: List[DocumentVersion] = []
    comments: List[DocumentComment] = []
    shares: List[DocumentShare] = []
    folder: Optional[DocumentFolder] = None

    class Config:
        from_attributes = True

class DocumentStats(BaseModel):
    total_documents: int
    total_size: int  # in bytes
    by_type: Dict[str, int]  # file_type: count
    by_month: Dict[str, int]  # YYYY-MM: count
    favorite_count: int
    archived_count: int
    shared_count: int
    total_folders: int
    total_tags: int
    most_used_tags: List[Dict[str, int]]  # [{"name": tag_name, "count": count}]

class DocumentUploadResponse(BaseModel):
    id: int
    upload_url: str
    expires_at: datetime 