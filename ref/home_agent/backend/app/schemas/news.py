from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl, EmailStr, constr

# Base schemas
class NewsCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class NewsArticleBase(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    source: str
    url: HttpUrl
    image_url: Optional[HttpUrl] = None
    category_id: int
    published_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class NewsPreferenceBase(BaseModel):
    preferred_sources: Optional[List[str]] = None
    excluded_sources: Optional[List[str]] = None
    preferred_languages: Optional[List[str]] = None
    notification_enabled: bool = True
    email_digest_enabled: bool = False
    email_digest_frequency: str = "daily"

class NewsBookmarkBase(BaseModel):
    article_id: int
    notes: Optional[str] = None

class NewsReadRecordBase(BaseModel):
    article_id: int
    read_duration: Optional[int] = None
    completed: bool = False

# Create schemas
class NewsCategoryCreate(NewsCategoryBase):
    pass

class NewsArticleCreate(NewsArticleBase):
    pass

class NewsPreferenceCreate(NewsPreferenceBase):
    pass

class NewsBookmarkCreate(NewsBookmarkBase):
    pass

class NewsReadRecordCreate(NewsReadRecordBase):
    pass

# Update schemas
class NewsCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = None
    category_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class NewsPreferenceUpdate(BaseModel):
    preferred_sources: Optional[List[str]] = None
    excluded_sources: Optional[List[str]] = None
    preferred_languages: Optional[List[str]] = None
    notification_enabled: Optional[bool] = None
    email_digest_enabled: Optional[bool] = None
    email_digest_frequency: Optional[str] = None

class NewsBookmarkUpdate(BaseModel):
    notes: Optional[str] = None

# Response schemas
class NewsCategory(NewsCategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NewsArticle(NewsArticleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class NewsArticleWithDetails(NewsArticle):
    category: NewsCategory
    bookmark_count: int
    read_count: int

    class Config:
        from_attributes = True

class NewsPreference(NewsPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NewsBookmark(NewsBookmarkBase):
    id: int
    user_id: int
    created_at: datetime
    article: NewsArticle

    class Config:
        from_attributes = True

class NewsReadRecord(NewsReadRecordBase):
    id: int
    user_id: int
    read_at: datetime
    article: NewsArticle

    class Config:
        from_attributes = True

# Additional schemas for specific operations
class NewsDigestSettings(BaseModel):
    email: EmailStr
    frequency: str
    time: str  # HH:MM format
    categories: List[int] = []

class NewsSearchParams(BaseModel):
    query: str
    categories: Optional[List[int]] = None
    sources: Optional[List[str]] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    sort_by: Optional[str] = "relevance"
    page: int = 1
    per_page: int = 20

class NewsStats(BaseModel):
    total_articles: int
    articles_by_category: Dict[str, int]
    articles_by_source: Dict[str, int]
    reading_time: int  # Total reading time in minutes
    completion_rate: float  # Percentage of completed articles 