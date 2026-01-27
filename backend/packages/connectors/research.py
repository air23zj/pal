"""
Research connector using Serper.dev for web search.

Provides relevant web search results based on user topics and preferences.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx

from .base import BaseConnector, ConnectorResult
from packages.shared.schemas import BriefItem, Entity

logger = logging.getLogger(__name__)


class ResearchConnector(BaseConnector):
    """
    Web search research connector using Serper.dev.

    Searches for relevant information based on user topics and current context.
    """

    @property
    def source_name(self) -> str:
        """Return the name of this connector's source"""
        return "research"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Serper connector.

        Args:
            api_key: Serper API key (defaults to SERPER_SEARCH_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("SERPER_SEARCH_API_KEY")
        if not self.api_key:
            logger.warning("No Serper key provided - research searches will be disabled")

    async def connect(self) -> bool:
        """
        Establish connection to SerpApi.

        Returns:
            True if API key is configured, False otherwise
        """
        return self.is_available()

    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> ConnectorResult:
        """
        Fetch research results based on user preferences.

        Args:
            since: Timestamp to search from (not used for research)
            limit: Maximum number of results (not used for research)
            **kwargs: Should include user_preferences

        Returns:
            ConnectorResult with research items
        """
        from datetime import timezone
        import time

        user_preferences = kwargs.get('user_preferences', {})
        topics = user_preferences.get('topics', [])

        if not topics:
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="ok",
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )

        try:
            brief_items = await self.fetch_research(topics, since or datetime.now(timezone.utc), limit or 5)

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
            logger.error(f"Research fetch failed: {e}")
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="error",
                error_message=str(e),
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )

    def is_available(self) -> bool:
        """Check if SerpApi is configured"""
        return bool(self.api_key)

    async def fetch_research(
        self,
        topics: List[str],
        since_timestamp: datetime,
        max_results: int = 5
    ) -> List[BriefItem]:
        """
        Search for relevant research based on user topics.

        Args:
            topics: List of topics to search for
            since_timestamp: Only return results newer than this timestamp
            max_results: Maximum number of results per topic

        Returns:
            List of BriefItem objects with research findings
        """
        if not self.is_available():
            logger.info("Serper not configured, skipping research")
            return []

        results = []

        for topic in topics[:3]:  # Limit to first 3 topics to avoid rate limits
            try:
                logger.info(f"Searching for research on: {topic}")

                # Build search query
                query = f"{topic} latest developments"

                # Call SerpApi
                search_results = await self._search_google(query, max_results)

                for item in search_results:
                    # Create BriefItem
                    brief_item = BriefItem(
                        item_ref=f"research_{topic}_{hash(item.get('link', ''))}",
                        source="research",
                        type="research",
                        timestamp_utc=datetime.now(timezone.utc).isoformat(),
                        title=item.get("title", "Research Finding"),
                        summary=item.get("snippet", item.get("title", "No summary available")),
                        why_it_matters="pending",  # Will be filled by LLM synthesizer
                        entities=[
                            Entity(kind="topic", key=topic),
                        ],
                        novelty={"label": "NEW", "reason": "research_search", "first_seen_utc": datetime.now(timezone.utc).isoformat()},
                        ranking={
                            "relevance_score": 0.7,  # Research is generally relevant
                            "urgency_score": 0.3,    # Not typically urgent
                            "credibility_score": 0.8, # Web search results
                            "impact_score": 0.6,     # Can be impactful
                            "actionability_score": 0.4, # May require further research
                            "final_score": 0.6
                        },
                        evidence=[],
                        suggested_actions=[]
                    )

                    # Add metadata
                    brief_item.metadata = {
                        "search_query": query,
                        "source_url": item.get("link", ""),
                        "display_link": item.get("displayLink", ""),
                        "search_topic": topic
                    }

                    results.append(brief_item)

            except Exception as e:
                logger.error(f"Error searching for topic '{topic}': {e}")
                continue

        logger.info(f"Found {len(results)} research items")
        return results

    async def _search_google(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform Google search using Serper.dev.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search result dictionaries
        """
        if not self.api_key:
            raise ValueError("Serper API key not configured")

        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            "q": query,
            "num": num_results,
            "gl": "us",
            "hl": "en"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://google.serper.dev/search", json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Extract organic results (Serper uses "organic" key)
            results = []
            if "organic" in data:
                for result in data["organic"][:num_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "displayLink": result.get("displayLink", "")  # Note: Serper uses displayLink
                    })

            return results

    async def fetch_messages(
        self,
        since: datetime,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[BriefItem]:
        """
        Main connector interface - fetch research based on user preferences.

        Args:
            since: Timestamp to search from
            user_preferences: User preferences including topics

        Returns:
            List of research BriefItems
        """
        if not user_preferences or not user_preferences.get("topics"):
            logger.info("No topics specified for research, skipping")
            return []

        topics = user_preferences.get("topics", [])
        return await self.fetch_research(topics, since)