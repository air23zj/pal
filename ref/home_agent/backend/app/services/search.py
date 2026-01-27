from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
import time

from app.models.search import SearchType, SearchHistory, SearchSettings, SearchIndex
from app.schemas.search import (
    SearchRequest, SearchResponse, SearchResult, SearchFilters,
    SearchSettingsCreate, SearchSettingsUpdate, SearchStats
)

class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, user_id: int, search_request: SearchRequest) -> SearchResponse:
        start_time = time.time()
        
        # Get user's search settings
        settings = self.get_or_create_settings(user_id)
        
        # Apply search type filter
        search_type = search_request.search_type or settings.default_search_type
        excluded_types = settings.excluded_types or []
        
        # Build base query
        query = self.db.query(SearchIndex)
        
        # Apply content type filter
        if search_type != SearchType.ALL:
            query = query.filter(SearchIndex.content_type == search_type)
        elif excluded_types:
            query = query.filter(SearchIndex.content_type.notin_(excluded_types))
        
        # Apply text search
        query = query.filter(
            or_(
                SearchIndex.title.ilike(f"%{search_request.query}%"),
                SearchIndex.description.ilike(f"%{search_request.query}%"),
                SearchIndex.keywords.contains([search_request.query])
            )
        )
        
        # Apply additional filters
        if search_request.filters:
            query = self._apply_filters(query, search_request.filters)
        
        # Calculate total results and results by type
        total_results = query.count()
        results_by_type = dict(
            query.with_entities(
                SearchIndex.content_type,
                func.count(SearchIndex.id)
            ).group_by(SearchIndex.content_type).all()
        )
        
        # Apply sorting
        query = self._apply_sorting(query, search_request.sort_by, search_request.sort_order)
        
        # Apply pagination
        query = query.offset((search_request.page - 1) * search_request.per_page)
        query = query.limit(search_request.per_page)
        
        # Get results
        results = [
            SearchResult(
                id=result.id,
                content_type=result.content_type,
                content_id=result.content_id,
                title=result.title,
                description=result.description,
                url=self._get_content_url(result.content_type, result.content_id),
                created_at=result.created_at,
                updated_at=result.updated_at,
                metadata=result.metadata,
                relevance_score=self._calculate_relevance_score(
                    result, search_request.query
                )
            )
            for result in query.all()
        ]
        
        # Calculate facets
        facets = self._calculate_facets(query)
        
        # Save search history if enabled
        if settings.save_search_history:
            self._save_search_history(
                user_id=user_id,
                query=search_request.query,
                search_type=search_type,
                filters=search_request.filters.dict() if search_request.filters else None,
                results_count=total_results
            )
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            query=search_request.query,
            total_results=total_results,
            results_by_type=results_by_type,
            results=results,
            facets=facets,
            execution_time=execution_time
        )

    def _apply_filters(self, query, filters: SearchFilters):
        if filters.date_from:
            query = query.filter(SearchIndex.created_at >= filters.date_from)
        if filters.date_to:
            query = query.filter(SearchIndex.created_at <= filters.date_to)
        if filters.categories:
            query = query.filter(SearchIndex.metadata['category'].astext.in_(filters.categories))
        if filters.tags:
            query = query.filter(SearchIndex.metadata['tags'].contains(filters.tags))
        if filters.owner_id:
            query = query.filter(SearchIndex.metadata['owner_id'].astext.cast(Integer) == filters.owner_id)
        if filters.shared_with_me is not None:
            query = query.filter(SearchIndex.metadata['shared_with'].contains([filters.owner_id]))
        return query

    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        if sort_by == "date":
            order_by = desc(SearchIndex.created_at) if sort_order == "desc" else SearchIndex.created_at
        elif sort_by == "title":
            order_by = desc(SearchIndex.title) if sort_order == "desc" else SearchIndex.title
        else:  # relevance - implement your relevance scoring logic
            order_by = desc(SearchIndex.created_at)  # Default to date for now
        return query.order_by(order_by)

    def _calculate_facets(self, query) -> Dict[str, Dict[str, int]]:
        return {
            "content_type": dict(
                query.with_entities(
                    SearchIndex.content_type,
                    func.count(SearchIndex.id)
                ).group_by(SearchIndex.content_type).all()
            ),
            "created_at": self._calculate_date_facets(query),
            # Add more facets as needed
        }

    def _calculate_date_facets(self, query) -> Dict[str, int]:
        now = datetime.utcnow()
        return {
            "last_24h": query.filter(SearchIndex.created_at >= now - timedelta(days=1)).count(),
            "last_week": query.filter(SearchIndex.created_at >= now - timedelta(weeks=1)).count(),
            "last_month": query.filter(SearchIndex.created_at >= now - timedelta(days=30)).count(),
            "older": query.filter(SearchIndex.created_at < now - timedelta(days=30)).count()
        }

    def _calculate_relevance_score(self, result: SearchIndex, query: str) -> float:
        # Implement your relevance scoring logic here
        # This is a simple example based on title match
        if query.lower() in result.title.lower():
            return 1.0
        elif result.description and query.lower() in result.description.lower():
            return 0.8
        elif result.keywords and query.lower() in [k.lower() for k in result.keywords]:
            return 0.6
        return 0.4

    def _get_content_url(self, content_type: SearchType, content_id: int) -> str:
        # Implement logic to generate URLs for different content types
        base_url = "/api/v1"
        return f"{base_url}/{content_type.value}/{content_id}"

    def _save_search_history(
        self,
        user_id: int,
        query: str,
        search_type: SearchType,
        filters: Optional[Dict[str, Any]] = None,
        results_count: int = 0
    ) -> SearchHistory:
        search_history = SearchHistory(
            user_id=user_id,
            query=query,
            search_type=search_type,
            filters=filters,
            results_count=results_count
        )
        self.db.add(search_history)
        self.db.commit()
        self.db.refresh(search_history)
        return search_history

    def get_search_history(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SearchHistory]:
        return (
            self.db.query(SearchHistory)
            .filter(SearchHistory.user_id == user_id)
            .order_by(desc(SearchHistory.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def clear_search_history(self, user_id: int) -> bool:
        self.db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).delete()
        self.db.commit()
        return True

    def get_or_create_settings(self, user_id: int) -> SearchSettings:
        settings = (
            self.db.query(SearchSettings)
            .filter(SearchSettings.user_id == user_id)
            .first()
        )
        if not settings:
            settings = SearchSettings(user_id=user_id)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings

    def update_settings(
        self,
        user_id: int,
        settings_in: SearchSettingsUpdate
    ) -> SearchSettings:
        settings = self.get_or_create_settings(user_id)
        
        for field, value in settings_in.dict(exclude_unset=True).items():
            setattr(settings, field, value)
        
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def get_search_stats(self, user_id: int) -> SearchStats:
        # Get total searches
        total_searches = (
            self.db.query(func.count(SearchHistory.id))
            .filter(SearchHistory.user_id == user_id)
            .scalar()
        )

        # Get searches by type
        searches_by_type = dict(
            self.db.query(
                SearchHistory.search_type,
                func.count(SearchHistory.id)
            )
            .filter(SearchHistory.user_id == user_id)
            .group_by(SearchHistory.search_type)
            .all()
        )

        # Get top queries
        top_queries = (
            self.db.query(
                SearchHistory.query,
                func.count(SearchHistory.id).label('count')
            )
            .filter(SearchHistory.user_id == user_id)
            .group_by(SearchHistory.query)
            .order_by(desc('count'))
            .limit(10)
            .all()
        )

        # Calculate average results
        avg_results = (
            self.db.query(func.avg(SearchHistory.results_count))
            .filter(SearchHistory.user_id == user_id)
            .scalar() or 0
        )

        # Get most used filters
        most_used_filters = {}
        filter_counts = (
            self.db.query(SearchHistory.filters)
            .filter(
                SearchHistory.user_id == user_id,
                SearchHistory.filters.isnot(None)
            )
            .all()
        )
        for filters in filter_counts:
            for key in filters[0].keys():
                most_used_filters[key] = most_used_filters.get(key, 0) + 1

        # Get recent search history
        search_history = (
            self.db.query(SearchHistory)
            .filter(SearchHistory.user_id == user_id)
            .order_by(desc(SearchHistory.created_at))
            .limit(10)
            .all()
        )

        return SearchStats(
            total_searches=total_searches,
            searches_by_type=searches_by_type,
            top_queries=[{"query": q, "count": c} for q, c in top_queries],
            average_results=float(avg_results),
            most_used_filters=most_used_filters,
            search_history=search_history
        ) 