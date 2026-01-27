from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.search import SearchService
from app.schemas.search import (
    SearchRequest, SearchResponse, SearchHistoryItem,
    SearchSettings, SearchSettingsUpdate, SearchStats
)

router = APIRouter()

@router.post("/", response_model=SearchResponse)
def search(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    search_request: SearchRequest
) -> SearchResponse:
    """
    Perform a search across all content types.
    """
    search_service = SearchService(db)
    return search_service.search(current_user.id, search_request)

@router.get("/history", response_model=List[SearchHistoryItem])
def get_search_history(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
) -> List[SearchHistoryItem]:
    """
    Get user's search history.
    """
    search_service = SearchService(db)
    return search_service.get_search_history(
        current_user.id,
        skip=skip,
        limit=limit
    )

@router.delete("/history")
def clear_search_history(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> bool:
    """
    Clear user's search history.
    """
    search_service = SearchService(db)
    return search_service.clear_search_history(current_user.id)

@router.get("/settings", response_model=SearchSettings)
def get_search_settings(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> SearchSettings:
    """
    Get user's search settings.
    """
    search_service = SearchService(db)
    return search_service.get_or_create_settings(current_user.id)

@router.put("/settings", response_model=SearchSettings)
def update_search_settings(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    settings_in: SearchSettingsUpdate
) -> SearchSettings:
    """
    Update user's search settings.
    """
    search_service = SearchService(db)
    return search_service.update_settings(current_user.id, settings_in)

@router.get("/stats", response_model=SearchStats)
def get_search_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> SearchStats:
    """
    Get user's search statistics.
    """
    search_service = SearchService(db)
    return search_service.get_search_stats(current_user.id) 