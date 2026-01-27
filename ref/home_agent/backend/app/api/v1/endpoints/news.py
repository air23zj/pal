from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.news import NewsService
from app.schemas.news import (
    NewsCategory, NewsArticle, NewsArticleWithDetails, NewsPreference,
    NewsBookmark, NewsReadRecord, NewsStats, NewsSearchParams,
    NewsDigestSettings, NewsCategoryCreate, NewsArticleCreate,
    NewsPreferenceCreate, NewsBookmarkCreate, NewsReadRecordCreate,
    NewsCategoryUpdate, NewsArticleUpdate, NewsPreferenceUpdate,
    NewsBookmarkUpdate
)

router = APIRouter()

# Category endpoints
@router.post("/categories", response_model=NewsCategory)
def create_category(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    category_in: NewsCategoryCreate
) -> NewsCategory:
    """
    Create a new news category.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    news_service = NewsService(db)
    return news_service.create_category(category_in)

@router.get("/categories", response_model=List[NewsCategory])
def get_categories(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
) -> List[NewsCategory]:
    """
    Retrieve news categories.
    """
    news_service = NewsService(db)
    return news_service.get_categories(skip=skip, limit=limit)

@router.get("/categories/{category_id}", response_model=NewsCategory)
def get_category(
    *,
    db: Session = Depends(deps.get_db),
    category_id: int
) -> NewsCategory:
    """
    Get a specific news category.
    """
    news_service = NewsService(db)
    category = news_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/categories/{category_id}", response_model=NewsCategory)
def update_category(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    category_id: int,
    category_in: NewsCategoryUpdate
) -> NewsCategory:
    """
    Update a news category.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    news_service = NewsService(db)
    category = news_service.update_category(category_id, category_in)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.delete("/categories/{category_id}")
def delete_category(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    category_id: int
) -> bool:
    """
    Delete a news category.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    news_service = NewsService(db)
    if not news_service.delete_category(category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    return True

# Article endpoints
@router.post("/articles", response_model=NewsArticle)
def create_article(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    article_in: NewsArticleCreate
) -> NewsArticle:
    """
    Create a new news article.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    news_service = NewsService(db)
    return news_service.create_article(article_in)

@router.get("/articles", response_model=List[NewsArticle])
def get_articles(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category_id: Optional[int] = None,
    source: Optional[str] = None
) -> List[NewsArticle]:
    """
    Retrieve news articles.
    """
    news_service = NewsService(db)
    return news_service.get_articles(
        skip=skip,
        limit=limit,
        category_id=category_id,
        source=source
    )

@router.get("/articles/{article_id}", response_model=NewsArticleWithDetails)
def get_article(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int
) -> NewsArticleWithDetails:
    """
    Get a specific news article.
    """
    news_service = NewsService(db)
    article = news_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.put("/articles/{article_id}", response_model=NewsArticle)
def update_article(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    article_id: int,
    article_in: NewsArticleUpdate
) -> NewsArticle:
    """
    Update a news article.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    news_service = NewsService(db)
    article = news_service.update_article(article_id, article_in)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.delete("/articles/{article_id}")
def delete_article(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    article_id: int
) -> bool:
    """
    Delete a news article.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    news_service = NewsService(db)
    if not news_service.delete_article(article_id):
        raise HTTPException(status_code=404, detail="Article not found")
    return True

# Preference endpoints
@router.get("/preferences", response_model=NewsPreference)
def get_preferences(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> NewsPreference:
    """
    Get user's news preferences.
    """
    news_service = NewsService(db)
    return news_service.get_or_create_preference(current_user.id)

@router.put("/preferences", response_model=NewsPreference)
def update_preferences(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    preference_in: NewsPreferenceUpdate
) -> NewsPreference:
    """
    Update user's news preferences.
    """
    news_service = NewsService(db)
    return news_service.update_preference(current_user.id, preference_in)

# Bookmark endpoints
@router.post("/bookmarks", response_model=NewsBookmark)
def create_bookmark(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    bookmark_in: NewsBookmarkCreate
) -> NewsBookmark:
    """
    Create a new bookmark.
    """
    news_service = NewsService(db)
    return news_service.create_bookmark(current_user.id, bookmark_in)

@router.get("/bookmarks", response_model=List[NewsBookmark])
def get_bookmarks(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
) -> List[NewsBookmark]:
    """
    Retrieve user's bookmarks.
    """
    news_service = NewsService(db)
    return news_service.get_user_bookmarks(current_user.id, skip=skip, limit=limit)

@router.delete("/bookmarks/{bookmark_id}")
def delete_bookmark(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    bookmark_id: int
) -> bool:
    """
    Delete a bookmark.
    """
    news_service = NewsService(db)
    if not news_service.delete_bookmark(current_user.id, bookmark_id):
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return True

# Read record endpoints
@router.post("/read-records", response_model=NewsReadRecord)
def create_read_record(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    record_in: NewsReadRecordCreate
) -> NewsReadRecord:
    """
    Create a new read record.
    """
    news_service = NewsService(db)
    return news_service.create_read_record(current_user.id, record_in)

@router.get("/read-records", response_model=List[NewsReadRecord])
def get_read_history(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
) -> List[NewsReadRecord]:
    """
    Retrieve user's read history.
    """
    news_service = NewsService(db)
    return news_service.get_user_read_history(current_user.id, skip=skip, limit=limit)

# Search endpoints
@router.post("/search", response_model=List[NewsArticle])
def search_articles(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    params: NewsSearchParams
) -> List[NewsArticle]:
    """
    Search news articles.
    """
    news_service = NewsService(db)
    return news_service.search_articles(params, current_user.id)

# Digest endpoints
@router.post("/digest", response_model=List[NewsArticle])
def get_news_digest(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    settings: NewsDigestSettings
) -> List[NewsArticle]:
    """
    Get personalized news digest.
    """
    news_service = NewsService(db)
    return news_service.get_news_digest(current_user.id, settings)

# Statistics endpoints
@router.get("/stats", response_model=NewsStats)
def get_user_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> NewsStats:
    """
    Get user's news statistics.
    """
    news_service = NewsService(db)
    return news_service.get_user_stats(current_user.id) 