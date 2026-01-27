from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from fastapi import HTTPException

from app.models.news import (
    NewsCategory, NewsArticle, NewsPreference, NewsBookmark,
    NewsReadRecord
)
from app.schemas.news import (
    NewsCategoryCreate, NewsArticleCreate, NewsPreferenceCreate,
    NewsBookmarkCreate, NewsReadRecordCreate, NewsSearchParams,
    NewsDigestSettings
)

class NewsService:
    def __init__(self, db: Session):
        self.db = db

    # Category methods
    def create_category(self, category_in: NewsCategoryCreate) -> NewsCategory:
        category = NewsCategory(**category_in.dict())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def get_category(self, category_id: int) -> Optional[NewsCategory]:
        return self.db.query(NewsCategory).filter(NewsCategory.id == category_id).first()

    def get_categories(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[NewsCategory]:
        return (
            self.db.query(NewsCategory)
            .order_by(NewsCategory.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_category(
        self,
        category_id: int,
        category_in: NewsCategoryCreate
    ) -> Optional[NewsCategory]:
        category = self.get_category(category_id)
        if not category:
            return None

        for field, value in category_in.dict(exclude_unset=True).items():
            setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> bool:
        category = self.get_category(category_id)
        if not category:
            return False

        self.db.delete(category)
        self.db.commit()
        return True

    # Article methods
    def create_article(self, article_in: NewsArticleCreate) -> NewsArticle:
        article = NewsArticle(**article_in.dict())
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def get_article(self, article_id: int) -> Optional[NewsArticle]:
        return self.db.query(NewsArticle).filter(NewsArticle.id == article_id).first()

    def get_articles(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        source: Optional[str] = None
    ) -> List[NewsArticle]:
        query = self.db.query(NewsArticle)

        if category_id:
            query = query.filter(NewsArticle.category_id == category_id)
        if source:
            query = query.filter(NewsArticle.source == source)

        return (
            query.order_by(desc(NewsArticle.published_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_article(
        self,
        article_id: int,
        article_in: NewsArticleCreate
    ) -> Optional[NewsArticle]:
        article = self.get_article(article_id)
        if not article:
            return None

        for field, value in article_in.dict(exclude_unset=True).items():
            setattr(article, field, value)

        self.db.commit()
        self.db.refresh(article)
        return article

    def delete_article(self, article_id: int) -> bool:
        article = self.get_article(article_id)
        if not article:
            return False

        self.db.delete(article)
        self.db.commit()
        return True

    # Preference methods
    def get_or_create_preference(
        self,
        user_id: int
    ) -> NewsPreference:
        preference = (
            self.db.query(NewsPreference)
            .filter(NewsPreference.user_id == user_id)
            .first()
        )
        if not preference:
            preference = NewsPreference(user_id=user_id)
            self.db.add(preference)
            self.db.commit()
            self.db.refresh(preference)
        return preference

    def update_preference(
        self,
        user_id: int,
        preference_in: NewsPreferenceCreate
    ) -> NewsPreference:
        preference = self.get_or_create_preference(user_id)

        for field, value in preference_in.dict(exclude_unset=True).items():
            setattr(preference, field, value)

        self.db.commit()
        self.db.refresh(preference)
        return preference

    # Bookmark methods
    def create_bookmark(
        self,
        user_id: int,
        bookmark_in: NewsBookmarkCreate
    ) -> NewsBookmark:
        bookmark = NewsBookmark(**bookmark_in.dict(), user_id=user_id)
        self.db.add(bookmark)
        self.db.commit()
        self.db.refresh(bookmark)
        return bookmark

    def get_user_bookmarks(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[NewsBookmark]:
        return (
            self.db.query(NewsBookmark)
            .filter(NewsBookmark.user_id == user_id)
            .order_by(desc(NewsBookmark.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete_bookmark(
        self,
        user_id: int,
        bookmark_id: int
    ) -> bool:
        bookmark = (
            self.db.query(NewsBookmark)
            .filter(
                NewsBookmark.id == bookmark_id,
                NewsBookmark.user_id == user_id
            )
            .first()
        )
        if not bookmark:
            return False

        self.db.delete(bookmark)
        self.db.commit()
        return True

    # Read record methods
    def create_read_record(
        self,
        user_id: int,
        record_in: NewsReadRecordCreate
    ) -> NewsReadRecord:
        record = NewsReadRecord(**record_in.dict(), user_id=user_id)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_user_read_history(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[NewsReadRecord]:
        return (
            self.db.query(NewsReadRecord)
            .filter(NewsReadRecord.user_id == user_id)
            .order_by(desc(NewsReadRecord.read_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    # Search methods
    def search_articles(
        self,
        params: NewsSearchParams,
        user_id: Optional[int] = None
    ) -> List[NewsArticle]:
        query = self.db.query(NewsArticle)

        if params.query:
            query = query.filter(
                NewsArticle.title.ilike(f"%{params.query}%") |
                NewsArticle.content.ilike(f"%{params.query}%")
            )

        if params.categories:
            query = query.filter(NewsArticle.category_id.in_(params.categories))

        if params.sources:
            query = query.filter(NewsArticle.source.in_(params.sources))

        if params.from_date:
            query = query.filter(NewsArticle.published_at >= params.from_date)

        if params.to_date:
            query = query.filter(NewsArticle.published_at <= params.to_date)

        if params.sort_by == "relevance" and params.query:
            # Implement relevance sorting logic
            pass
        else:
            query = query.order_by(desc(NewsArticle.published_at))

        return query.offset((params.page - 1) * params.per_page).limit(params.per_page).all()

    # Digest methods
    def get_news_digest(
        self,
        user_id: int,
        settings: NewsDigestSettings
    ) -> List[NewsArticle]:
        preference = self.get_or_create_preference(user_id)
        
        query = self.db.query(NewsArticle)

        if settings.categories:
            query = query.filter(NewsArticle.category_id.in_(settings.categories))

        if preference.preferred_sources:
            query = query.filter(NewsArticle.source.in_(preference.preferred_sources))

        if preference.excluded_sources:
            query = query.filter(~NewsArticle.source.in_(preference.excluded_sources))

        # Get articles from the appropriate time range based on frequency
        if settings.frequency == "daily":
            from_date = datetime.utcnow() - timedelta(days=1)
        elif settings.frequency == "weekly":
            from_date = datetime.utcnow() - timedelta(weeks=1)
        else:  # monthly
            from_date = datetime.utcnow() - timedelta(days=30)

        query = query.filter(NewsArticle.published_at >= from_date)

        return query.order_by(desc(NewsArticle.published_at)).all()

    # Statistics methods
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        # Get total articles read
        total_read = (
            self.db.query(func.count(NewsReadRecord.id))
            .filter(NewsReadRecord.user_id == user_id)
            .scalar()
        )

        # Get articles by category
        articles_by_category = (
            self.db.query(
                NewsCategory.name,
                func.count(NewsReadRecord.id)
            )
            .join(NewsArticle, NewsArticle.category_id == NewsCategory.id)
            .join(NewsReadRecord, NewsReadRecord.article_id == NewsArticle.id)
            .filter(NewsReadRecord.user_id == user_id)
            .group_by(NewsCategory.name)
            .all()
        )

        # Get articles by source
        articles_by_source = (
            self.db.query(
                NewsArticle.source,
                func.count(NewsReadRecord.id)
            )
            .join(NewsReadRecord, NewsReadRecord.article_id == NewsArticle.id)
            .filter(NewsReadRecord.user_id == user_id)
            .group_by(NewsArticle.source)
            .all()
        )

        # Calculate total reading time
        total_reading_time = (
            self.db.query(func.sum(NewsReadRecord.read_duration))
            .filter(NewsReadRecord.user_id == user_id)
            .scalar() or 0
        )

        # Calculate completion rate
        completed_articles = (
            self.db.query(func.count(NewsReadRecord.id))
            .filter(
                NewsReadRecord.user_id == user_id,
                NewsReadRecord.completed == True
            )
            .scalar()
        )
        completion_rate = (completed_articles / total_read * 100) if total_read > 0 else 0

        return {
            "total_articles": total_read,
            "articles_by_category": dict(articles_by_category),
            "articles_by_source": dict(articles_by_source),
            "reading_time": total_reading_time // 60,  # Convert to minutes
            "completion_rate": completion_rate
        } 