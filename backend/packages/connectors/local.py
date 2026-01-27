"""
Local connector using SerpApi Yelp Search API.

Provides local business recommendations, reviews, and service discovery.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import httpx

from .base import BaseConnector, ConnectorResult
from packages.shared.schemas import BriefItem, Entity

logger = logging.getLogger(__name__)


class LocalConnector(BaseConnector):
    """
    Yelp Search connector using SerpApi.

    Searches for local businesses, restaurants, and services with reviews.
    """

    @property
    def source_name(self) -> str:
        """Return the name of this connector's source"""
        return "local"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpApi Yelp Search connector.

        Args:
            api_key: SerpApi API key (defaults to SERPAPI_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("No SerpApi key provided - local business searches will be disabled")

    async def connect(self) -> bool:
        """
        Establish connection to SerpApi.

        Returns:
            True if API key is configured, False otherwise
        """
        return self.is_available()

    def is_available(self) -> bool:
        """
        Check if the connector is available (has API key).

        Returns:
            True if SerpApi key is configured, False otherwise
        """
        return bool(self.api_key)

    async def search_local_businesses(
        self,
        query: str,
        location: str = "New York",
        max_results: int = 5
    ) -> List[BriefItem]:
        """
        Search for local businesses on Yelp.

        Args:
            query: Search query (e.g., "coffee shops", "plumbers", "restaurants")
            location: Location to search in
            max_results: Maximum number of business results to return

        Returns:
            List of BriefItem objects with local business information
        """
        if not self.is_available():
            logger.info("SerpApi not configured, skipping local business search")
            return []

        results = []

        try:
            logger.info(f"Searching Yelp for: {query} in {location}")

            business_data = await self._search_yelp(
                query, location, max_results
            )

            for business in business_data[:max_results]:
                # Create BriefItem for each local business
                brief_item = BriefItem(
                    item_ref=f"local_{business.get('place_ids', [''])[0] if business.get('place_ids') else hash(str(business))}_{hash(str(business))}",
                    source="local",
                    type="local_business",
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    title=f"{business.get('title', 'Unknown Business')} - Yelp",
                    summary=self._format_business_summary(business),
                    why_it_matters="pending",  # Will be filled by LLM synthesizer
                    entities=[
                        Entity(kind="business", key=business.get('title', '')),
                        Entity(kind="location", key=location),
                    ],
                    novelty={"label": "NEW", "reason": "local_business_search", "first_seen_utc": datetime.now(timezone.utc).isoformat()},
                    ranking={
                        "relevance_score": 0.9,  # Local business recommendations are highly relevant
                        "urgency_score": 0.6,    # Local services have moderate urgency
                        "credibility_score": 0.9,  # Yelp reviews are user-generated and reliable
                        "impact_score": 0.8,      # Local business choices have high impact
                        "actionability_score": 0.9, # Can lead to immediate local actions
                        "final_score": 0.8
                    },
                    evidence=[],
                    suggested_actions=[]
                )

                # Add local business metadata
                brief_item.metadata = {
                    "business_name": business.get("title", ""),
                    "place_ids": business.get("place_ids", []),
                    "categories": business.get("categories", []),
                    "price_range": business.get("price", ""),
                    "rating": business.get("rating", 0),
                    "reviews_count": business.get("reviews", 0),
                    "location": location,
                    "neighborhoods": business.get("neighborhoods", ""),
                    "phone": business.get("phone", ""),
                    "snippet": business.get("snippet", ""),
                    "service_options": business.get("service_options", {}),
                    "highlights": business.get("highlights", []),
                    "thumbnail": business.get("thumbnail", ""),
                    "link": business.get("link", ""),
                    "search_query": query,
                }

                results.append(brief_item)

        except Exception as e:
            logger.error(f"Error searching Yelp for {query}: {e}")
            return []

        logger.info(f"Found {len(results)} local businesses for {query}")
        return results

    async def _search_yelp(
        self,
        query: str,
        location: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search Yelp using SerpApi.

        Args:
            query: Search query
            location: Location for search
            max_results: Maximum results to return

        Returns:
            List of business information from Yelp
        """
        if not self.api_key:
            raise ValueError("SerpApi key not configured")

        params = {
            "api_key": self.api_key,
            "engine": "yelp",
            "find_desc": query,
            "find_loc": location,
            "start": 0,  # Start from first result
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://serpapi.com/search", params=params)
            response.raise_for_status()

            data = response.json()

            # Extract organic results (main business listings)
            businesses = data.get("organic_results", [])
            return businesses

    def _format_business_summary(self, business: Dict[str, Any]) -> str:
        """
        Format business information into a readable summary.

        Args:
            business: Business data from Yelp API

        Returns:
            Formatted summary string
        """
        title = business.get("title", "Unknown Business")
        rating = business.get("rating", 0)
        reviews = business.get("reviews", 0)
        price = business.get("price", "")
        categories = business.get("categories", [])
        neighborhoods = business.get("neighborhoods", "")
        snippet = business.get("snippet", "")
        highlights = business.get("highlights", [])

        summary = f"{title}"

        if neighborhoods:
            summary += f" in {neighborhoods}"

        if rating > 0:
            summary += f" - {rating}/5 stars"

        if reviews > 0:
            summary += f" from {reviews} reviews"

        if price:
            summary += f" ({price})"

        # Add category information
        if categories:
            category_names = [cat.get("title", "") for cat in categories if cat.get("title")]
            if category_names:
                summary += f" - {', '.join(category_names[:2])}"  # Show first 2 categories

        # Add highlights if available
        if highlights:
            summary += f" - Highlights: {', '.join(highlights)}"

        # Add snippet if available (truncated)
        if snippet:
            truncated_snippet = snippet[:100] + "..." if len(snippet) > 100 else snippet
            summary += f" - {truncated_snippet}"

        return summary

    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> ConnectorResult:
        """
        Main connector interface - fetch local business information based on user preferences.

        Args:
            since: Timestamp to search from
            limit: Maximum number of results
            **kwargs: Should include user_preferences

        Returns:
            ConnectorResult with local business information
        """
        user_preferences = kwargs.get('user_preferences', {})
        local_interests = user_preferences.get('local_interests', [])
        local_services_needed = user_preferences.get('local_services_needed', [])

        if not local_interests and not local_services_needed:
            logger.info("No local interests or services specified for local business search, skipping")
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="ok",
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )

        all_businesses = []

        # Search for places based on local interests
        for interest in local_interests[:2]:  # Limit to avoid rate limits
            try:
                interest_results = await self.search_local_businesses(
                    interest, "New York", limit or 3
                )
                all_businesses.extend(interest_results)
            except Exception as e:
                logger.error(f"Error fetching local businesses for interest {interest}: {e}")
                continue

        # Search for specific services needed
        for service in local_services_needed[:2]:  # Limit to avoid rate limits
            try:
                service_name = service.get('service_type', '')
                service_location = service.get('location', 'New York')

                if service_name:
                    service_results = await self.search_local_businesses(
                        service_name, service_location, limit or 3
                    )
                    all_businesses.extend(service_results)
            except Exception as e:
                logger.error(f"Error fetching local businesses for service {service}: {e}")
                continue

        # Convert BriefItem objects to dicts for ConnectorResult
        items = []
        for item in all_businesses:
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