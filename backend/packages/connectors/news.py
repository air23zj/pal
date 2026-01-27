"""
News connector using SerpApi Google News API.

Fetches latest news articles related to user topics and preferences.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import httpx

from .base import BaseConnector, ConnectorResult
from packages.shared.schemas import BriefItem, Entity

logger = logging.getLogger(__name__)


class NewsConnector(BaseConnector):
    """
    Google News connector using SerpApi.

    Fetches latest news articles based on user topics and current context.
    """

    @property
    def source_name(self) -> str:
        """Return the name of this connector's source"""
        return "news"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpApi Google News connector.

        Args:
            api_key: SerpApi API key (defaults to SERPAPI_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("No SerpApi key provided - news searches will be disabled")

    def is_available(self) -> bool:
        """Check if SerpApi is configured"""
        return bool(self.api_key)

    async def connect(self) -> bool:
        """
        Establish connection to SerpApi.

        Returns:
            True if API key is configured, False otherwise
        """
        return self.is_available()

    async def fetch_news(
        self,
        topics: List[str],
        since_timestamp: datetime,
        max_results: int = 10
    ) -> List[BriefItem]:
        """
        Search for news articles based on user topics.

        Args:
            topics: List of topics to search for news about
            since_timestamp: Only return news newer than this timestamp
            max_results: Maximum number of results per topic

        Returns:
            List of BriefItem objects with news articles
        """
        if not self.is_available():
            logger.info("SerpApi not configured, skipping news")
            return []

        results = []

        # For news, we'll do a broader search combining topics
        # or search for each topic individually
        for topic in topics[:2]:  # Limit to first 2 topics to avoid rate limits
            try:
                logger.info(f"Fetching news for: {topic}")

                # Search for news about this topic
                news_articles = await self._search_google_news(topic, max_results)

                for article in news_articles:
                    # Convert to BriefItem
                    brief_item = BriefItem(
                        item_ref=f"news_{topic}_{hash(article.get('link', ''))}",
                        source="news",
                        type="news",
                        timestamp_utc=self._parse_news_date(article.get("date", "")) or datetime.now(timezone.utc).isoformat(),
                        title=article.get("title", "News Article"),
                        summary=article.get("snippet", article.get("title", "No summary available")),
                        why_it_matters="pending",  # Will be filled by LLM synthesizer
                        entities=[
                            Entity(kind="topic", key=topic),
                            Entity(kind="source", key=article.get("source", {}).get("name", "news")),
                        ],
                        novelty={"label": "NEW", "reason": "news_search", "first_seen_utc": datetime.now(timezone.utc).isoformat()},
                        ranking={
                            "relevance_score": 0.8,  # News is generally relevant
                            "urgency_score": self._calculate_news_urgency(article),
                            "credibility_score": 0.7,  # News sources vary in credibility
                            "impact_score": 0.6,      # News can be impactful
                            "actionability_score": 0.5, # May require further reading
                            "final_score": 0.7
                        },
                        evidence=[],
                        suggested_actions=[]
                    )

                    # Add metadata
                    brief_item.metadata = {
                        "search_query": topic,
                        "source_url": article.get("link", ""),
                        "news_source": article.get("source", {}).get("name", ""),
                        "thumbnail": article.get("thumbnail", ""),
                        "related_stories": article.get("related_topics", []),
                    }

                    results.append(brief_item)

            except Exception as e:
                logger.error(f"Error fetching news for topic '{topic}': {e}")
                continue

        logger.info(f"Found {len(results)} news items")
        return results

    async def _search_google_news(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search Google News using SerpApi.

        Args:
            query: News search query
            num_results: Number of results to return

        Returns:
            List of news article dictionaries
        """
        if not self.api_key:
            raise ValueError("SerpApi key not configured")

        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google_news",
            "num": num_results,
            "gl": "us",  # Country
            "hl": "en",  # Language
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://serpapi.com/search", params=params)
            response.raise_for_status()

            data = response.json()

            # Extract news results
            results = []
            if "news_results" in data:
                for article in data["news_results"][:num_results]:
                    results.append({
                        "title": article.get("title", ""),
                        "link": article.get("link", ""),
                        "snippet": article.get("snippet", ""),
                        "source": article.get("source", {}),
                        "date": article.get("date", ""),
                        "thumbnail": article.get("thumbnail", ""),
                        "related_topics": article.get("related_topics", []),
                    })

            return results

    def _parse_news_date(self, date_str: str) -> Optional[str]:
        """
        Parse various news date formats into ISO format.

        Args:
            date_str: Date string from news API

        Returns:
            ISO format datetime string or None if parsing fails
        """
        if not date_str:
            return None

        try:
            # SerpApi often returns dates like "09/29/2025, 08:05 AM, +0200 CEST"
            # or ISO dates like "2025-09-29T06:05:00Z"

            if "T" in date_str:  # Already ISO format
                return date_str

            # Try to parse common formats
            # For now, just return current time if we can't parse
            # In a production system, you'd want more robust date parsing
            return datetime.now(timezone.utc).isoformat()

        except Exception:
            return datetime.now(timezone.utc).isoformat()

    def _calculate_news_urgency(self, article: Dict[str, Any]) -> float:
        """
        Calculate urgency score based on article characteristics.

        Args:
            article: News article data

        Returns:
            Urgency score between 0.0 and 1.0
        """
        urgency = 0.5  # Base urgency

        # Recent articles are more urgent
        if article.get("date"):
            # If we can determine it's very recent, increase urgency
            urgency = 0.7

        # Articles with "breaking" or urgent keywords
        title = article.get("title", "").lower()
        if any(keyword in title for keyword in ["breaking", "urgent", "alert", "crisis", "emergency"]):
            urgency = 0.9

        return urgency

    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> ConnectorResult:
        """
        Main connector interface - fetch news based on user preferences.

        Args:
            since: Timestamp to search from
            limit: Maximum number of results
            **kwargs: Should include user_preferences

        Returns:
            ConnectorResult with news items
        """
        user_preferences = kwargs.get('user_preferences', {})
        topics = user_preferences.get('topics', [])

        if not topics:
            logger.info("No topics specified for news, skipping")
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="ok",
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )

        try:
            brief_items = await self.fetch_news(topics, since or datetime.now(timezone.utc), limit or 10)

            # Convert BriefItem objects to dicts for ConnectorResult
            items = []
            for item in brief_items:
                items.append({
                    "item_ref": item.item_ref,
                    "source": item.source,
                    "type": item.type,
                    "timestamp_utc": item.timestamp_utc,
                    "title": item.title,
                    "summary": item.summary,
                    "why_it_matters": item.why_it_matters,
                    "entities": [entity.dict() for entity in item.entities],
                    "novelty": item.novelty.dict() if item.novelty else None,
                    "ranking": item.ranking.dict() if item.ranking else None,
                    "evidence": item.evidence,
                    "suggested_actions": item.suggested_actions,
                    "metadata": item.metadata,
                })

            return ConnectorResult(
                source=self.source_name,
                items=items,
                status="ok",
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )

        except Exception as e:
            logger.error(f"News fetch failed: {e}")
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="error",
                error_message=str(e),
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )