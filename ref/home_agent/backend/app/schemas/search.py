from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, conint

from app.models.search import SearchType

# Base schemas
class SearchFilters(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    owner_id: Optional[int] = None
    shared_with_me: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchSettingsBase(BaseModel):
    default_search_type: Optional[SearchType] = SearchType.ALL
    excluded_types: Optional[List[SearchType]] = None
    max_results_per_type: Optional[conint(ge=1, le=100)] = 10
    save_search_history: Optional[bool] = True
    personalized_results: Optional[bool] = True

# Create/Update schemas
class SearchSettingsCreate(SearchSettingsBase):
    pass

class SearchSettingsUpdate(SearchSettingsBase):
    pass

# Response schemas
class SearchHistoryItem(BaseModel):
    id: int
    query: str
    search_type: SearchType
    filters: Optional[Dict[str, Any]] = None
    results_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class SearchSettings(SearchSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SearchResult(BaseModel):
    id: int
    content_type: SearchType
    content_id: int
    title: str
    description: Optional[str] = None
    url: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    relevance_score: float

    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results_by_type: Dict[SearchType, int]
    results: List[SearchResult]
    facets: Dict[str, Dict[str, int]]
    execution_time: float

# Request schemas
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    search_type: Optional[SearchType] = SearchType.ALL
    filters: Optional[SearchFilters] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = "relevance"  # relevance, date, title
    sort_order: Optional[str] = "desc"  # asc, desc

class SearchStats(BaseModel):
    total_searches: int
    searches_by_type: Dict[SearchType, int]
    top_queries: List[Dict[str, Any]]
    average_results: float
    most_used_filters: Dict[str, int]
    search_history: List[SearchHistoryItem] 