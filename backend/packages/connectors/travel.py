"""
Travel connector using SerpApi TripAdvisor Search API.

Provides travel recommendations, hotel reviews, and attraction information.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import httpx

from .base import BaseConnector, ConnectorResult
from packages.shared.schemas import BriefItem, Entity

logger = logging.getLogger(__name__)


class TravelConnector(BaseConnector):
    """
    TripAdvisor Search connector using SerpApi.

    Searches for hotels, attractions, restaurants, and travel destinations.
    """

    @property
    def source_name(self) -> str:
        """Return the name of this connector's source"""
        return "travel"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpApi TripAdvisor Search connector.

        Args:
            api_key: SerpApi API key (defaults to SERPAPI_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("No SerpApi key provided - travel searches will be disabled")

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

    async def search_travel_destinations(
        self,
        query: str,
        place_type: Optional[str] = None,
        location: str = "New York",
        max_results: int = 5
    ) -> List[BriefItem]:
        """
        Search for travel destinations and attractions on TripAdvisor.

        Args:
            query: Search query (e.g., "luxury hotels", "attractions", "restaurants")
            place_type: Filter by place type (ACCOMMODATION, ATTRACTION, EATERY, etc.)
            location: Location to search in
            max_results: Maximum number of results to return

        Returns:
            List of BriefItem objects with travel destination information
        """
        if not self.is_available():
            logger.info("SerpApi not configured, skipping travel search")
            return []

        results = []

        try:
            logger.info(f"Searching TripAdvisor for: {query} in {location}")

            travel_data = await self._search_tripadvisor(
                query, place_type, location, max_results
            )

            for place in travel_data[:max_results]:
                # Create BriefItem for each travel destination
                brief_item = BriefItem(
                    item_ref=f"travel_{place.get('place_id', '')}_{hash(str(place))}",
                    source="travel",
                    type="travel_destination",
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    title=f"{place.get('title', 'Unknown Place')} - TripAdvisor",
                    summary=self._format_place_summary(place),
                    why_it_matters="pending",  # Will be filled by LLM synthesizer
                    entities=[
                        Entity(kind="location", key=place.get('location', location)),
                        Entity(kind="attraction", key=place.get('title', '')),
                    ],
                    novelty={"label": "NEW", "reason": "travel_search", "first_seen_utc": datetime.now(timezone.utc).isoformat()},
                    ranking={
                        "relevance_score": 0.9,  # Travel recommendations are highly relevant
                        "urgency_score": 0.5,    # Travel planning has moderate urgency
                        "credibility_score": 0.9,  # TripAdvisor data is user-generated and reliable
                        "impact_score": 0.8,      # Travel decisions have high impact
                        "actionability_score": 0.7, # Can lead to travel bookings
                        "final_score": 0.8
                    },
                    evidence=[],
                    suggested_actions=[]
                )

                # Add travel destination metadata
                brief_item.metadata = {
                    "place_id": place.get("place_id", ""),
                    "place_type": place.get("place_type", ""),
                    "title": place.get("title", ""),
                    "location": place.get("location", ""),
                    "rating": place.get("rating", 0),
                    "reviews_count": place.get("reviews", 0),
                    "description": place.get("description", ""),
                    "thumbnail": place.get("thumbnail", ""),
                    "link": place.get("link", ""),
                    "highlighted_review": place.get("highlighted_review", {}),
                    "search_query": query,
                }

                results.append(brief_item)

        except Exception as e:
            logger.error(f"Error searching TripAdvisor for {query}: {e}")
            return []

        logger.info(f"Found {len(results)} travel destinations for {query}")
        return results

    async def _search_tripadvisor(
        self,
        query: str,
        place_type: Optional[str] = None,
        location: str = "New York",
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search TripAdvisor using SerpApi.

        Args:
            query: Search query
            place_type: Filter by place type
            location: Location for search
            max_results: Maximum results to return

        Returns:
            List of place information from TripAdvisor
        """
        if not self.api_key:
            raise ValueError("SerpApi key not configured")

        params = {
            "api_key": self.api_key,
            "engine": "tripadvisor_search",
            "q": f"{query} {location}",
            "limit": max_results,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://serpapi.com/search", params=params)
            response.raise_for_status()

            data = response.json()

            # Extract places from the response
            places = data.get("places", [])
            return places

    def _format_place_summary(self, place: Dict[str, Any]) -> str:
        """
        Format place information into a readable summary.

        Args:
            place: Place data from TripAdvisor API

        Returns:
            Formatted summary string
        """
        title = place.get("title", "Unknown Place")
        rating = place.get("rating", 0)
        reviews = place.get("reviews", 0)
        location = place.get("location", "")
        place_type = place.get("place_type", "")
        description = place.get("description", "")

        summary = f"{title}"
        if location:
            summary += f" in {location}"

        if rating > 0:
            summary += f" - {rating}/5 stars"

        if reviews > 0:
            summary += f" from {reviews} reviews"

        if place_type:
            # Convert place_type to more readable format
            type_map = {
                "ACCOMMODATION": "Hotel",
                "ATTRACTION": "Attraction",
                "EATERY": "Restaurant",
                "GEO": "Location",
                "VACATION_RENTAL": "Vacation Rental",
                "AIRLINE": "Airline",
                "ATTRACTION_PRODUCT": "Tour"
            }
            readable_type = type_map.get(place_type, place_type)
            summary += f" ({readable_type})"

        # Add truncated description if available
        if description:
            truncated_desc = description[:150] + "..." if len(description) > 150 else description
            summary += f" - {truncated_desc}"

        # Add highlighted review info if available
        highlighted = place.get("highlighted_review", {})
        if highlighted.get("mention_count", 0) > 0:
            mention_count = highlighted["mention_count"]
            summary += f" - {mention_count} reviews mention this place"

        return summary

    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> ConnectorResult:
        """
        Main connector interface - fetch travel information based on user preferences.

        Args:
            since: Timestamp to search from
            limit: Maximum number of results
            **kwargs: Should include user_preferences

        Returns:
            ConnectorResult with travel information
        """
        user_preferences = kwargs.get('user_preferences', {})
        travel_interests = user_preferences.get('travel_interests', [])
        upcoming_destinations = user_preferences.get('upcoming_destinations', [])

        if not travel_interests and not upcoming_destinations:
            logger.info("No travel interests or destinations specified for travel search, skipping")
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="ok",
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )

        all_travel = []

        # Search for places based on travel interests
        for interest in travel_interests[:2]:  # Limit to avoid rate limits
            try:
                interest_results = await self.search_travel_destinations(
                    interest, None, "New York", limit or 3
                )
                all_travel.extend(interest_results)
            except Exception as e:
                logger.error(f"Error fetching travel info for interest {interest}: {e}")
                continue

        # Search for specific destinations
        for destination in upcoming_destinations[:2]:  # Limit to avoid rate limits
            try:
                dest_name = destination.get('name', '')
                dest_location = destination.get('location', 'New York')
                place_type = destination.get('type', None)  # e.g., "ACCOMMODATION", "ATTRACTION"

                if dest_name:
                    dest_results = await self.search_travel_destinations(
                        dest_name, place_type, dest_location, limit or 3
                    )
                    all_travel.extend(dest_results)
            except Exception as e:
                logger.error(f"Error fetching travel info for destination {destination}: {e}")
                continue

        # Convert BriefItem objects to dicts for ConnectorResult
        items = []
        for item in all_travel:
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