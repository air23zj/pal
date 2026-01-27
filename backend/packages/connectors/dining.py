"""
Dining connector using SerpApi OpenTable Reviews API.

Provides restaurant reviews, ratings, and dining recommendations.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import httpx

from .base import BaseConnector, ConnectorResult
from packages.shared.schemas import BriefItem, Entity

logger = logging.getLogger(__name__)


class DiningConnector(BaseConnector):
    """
    OpenTable Reviews connector using SerpApi.

    Retrieves restaurant reviews, ratings, and dining insights.
    """

    @property
    def source_name(self) -> str:
        """Return the name of this connector's source"""
        return "dining"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpApi OpenTable Reviews connector.

        Args:
            api_key: SerpApi API key (defaults to SERPAPI_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("No SerpApi key provided - dining reviews will be disabled")

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

    async def search_restaurant_reviews(
        self,
        restaurant_name: str,
        location: str = "New York",
        max_reviews: int = 5
    ) -> List[BriefItem]:
        """
        Search for restaurant reviews on OpenTable.

        Args:
            restaurant_name: Name of the restaurant to search for
            location: Location/city for the search
            max_reviews: Maximum number of review items to return

        Returns:
            List of BriefItem objects with restaurant review information
        """
        if not self.is_available():
            logger.info("SerpApi not configured, skipping restaurant review search")
            return []

        results = []

        try:
            logger.info(f"Searching reviews for restaurant: {restaurant_name} in {location}")

            reviews_data = await self._search_opentable_reviews(
                restaurant_name, location, max_reviews
            )

            if not reviews_data:
                logger.info(f"No reviews found for {restaurant_name}")
                return []

            # Create summary item with overall ratings
            summary_item = BriefItem(
                item_ref=f"dining_summary_{restaurant_name.replace(' ', '_').lower()}_{hash(str(reviews_data))}",
                source="dining",
                type="restaurant_summary",
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                title=f"{restaurant_name} - Restaurant Review Summary",
                summary=self._format_restaurant_summary(reviews_data),
                why_it_matters="pending",  # Will be filled by LLM synthesizer
                entities=[
                    Entity(kind="restaurant", key=restaurant_name),
                    Entity(kind="location", key=location),
                ],
                novelty={"label": "NEW", "reason": "restaurant_review_search", "first_seen_utc": datetime.now(timezone.utc).isoformat()},
                ranking={
                    "relevance_score": 0.8,  # Restaurant reviews are highly relevant for dining decisions
                    "urgency_score": 0.4,    # Reviews don't change rapidly
                    "credibility_score": 0.9,  # OpenTable reviews are from verified diners
                    "impact_score": 0.7,      # Dining choices have moderate impact
                    "actionability_score": 0.8, # Can lead to restaurant reservations
                    "final_score": 0.7
                },
                evidence=[],
                suggested_actions=[]
            )

            # Add restaurant summary metadata
            summary_item.metadata = {
                "restaurant_name": restaurant_name,
                "location": location,
                "reviews_count": reviews_data.get("reviews_summary", {}).get("reviews_count", 0),
                "overall_rating": reviews_data.get("reviews_summary", {}).get("ratings_summary", {}).get("overall", 0),
                "food_rating": reviews_data.get("reviews_summary", {}).get("ratings_summary", {}).get("food", 0),
                "service_rating": reviews_data.get("reviews_summary", {}).get("ratings_summary", {}).get("service", 0),
                "ambience_rating": reviews_data.get("reviews_summary", {}).get("ratings_summary", {}).get("ambience", 0),
                "value_rating": reviews_data.get("reviews_summary", {}).get("ratings_summary", {}).get("value", 0),
                "noise_level": reviews_data.get("reviews_summary", {}).get("ratings_summary", {}).get("noise", ""),
                "ai_summary": reviews_data.get("reviews_summary", {}).get("ai_summary", ""),
            }

            results.append(summary_item)

            # Create individual review items
            reviews = reviews_data.get("reviews", [])[:max_reviews]
            for review in reviews:
                review_item = BriefItem(
                    item_ref=f"dining_review_{review.get('id', '')}_{hash(str(review))}",
                    source="dining",
                    type="restaurant_review",
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    title=f"Review of {restaurant_name}",
                    summary=self._format_review_summary(review, restaurant_name),
                    why_it_matters="pending",  # Will be filled by LLM synthesizer
                    entities=[
                        Entity(kind="restaurant", key=restaurant_name),
                        Entity(kind="person", key=review.get("user", {}).get("name", "")),
                    ],
                    novelty={"label": "NEW", "reason": "restaurant_review", "first_seen_utc": datetime.now(timezone.utc).isoformat()},
                    ranking={
                        "relevance_score": 0.7,
                        "urgency_score": 0.3,
                        "credibility_score": 0.8,
                        "impact_score": 0.6,
                        "actionability_score": 0.6,
                        "final_score": 0.6
                    },
                    evidence=[],
                    suggested_actions=[]
                )

                # Add review metadata
                review_item.metadata = {
                    "restaurant_name": restaurant_name,
                    "review_id": review.get("id", ""),
                    "reviewer_name": review.get("user", {}).get("name", ""),
                    "reviewer_location": review.get("user", {}).get("location", ""),
                    "reviewer_review_count": review.get("user", {}).get("number_of_reviews", 0),
                    "dined_at": review.get("dined_at", ""),
                    "submitted_at": review.get("submitted_at", ""),
                    "overall_rating": review.get("rating", {}).get("overall", 0),
                    "food_rating": review.get("rating", {}).get("food", 0),
                    "service_rating": review.get("rating", {}).get("service", 0),
                    "ambience_rating": review.get("rating", {}).get("ambience", 0),
                    "value_rating": review.get("rating", {}).get("value", 0),
                    "noise_rating": review.get("rating", {}).get("noise", ""),
                    "has_images": len(review.get("images", [])) > 0,
                    "has_response": "response" in review,
                }

                results.append(review_item)

        except Exception as e:
            logger.error(f"Error searching reviews for {restaurant_name}: {e}")
            return []

        logger.info(f"Found {len(results)} dining items for {restaurant_name}")
        return results

    async def _search_opentable_reviews(
        self,
        restaurant_name: str,
        location: str,
        max_reviews: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Search OpenTable reviews using SerpApi.

        Args:
            restaurant_name: Name of restaurant to search
            location: Location for search
            max_reviews: Maximum reviews to fetch

        Returns:
            Reviews data from OpenTable API
        """
        if not self.api_key:
            raise ValueError("SerpApi key not configured")

        # First, find the restaurant to get its OpenTable domain/place_id
        search_params = {
            "api_key": self.api_key,
            "engine": "opentable",
            "query": f"{restaurant_name} {location}",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Search for restaurant
            search_response = await client.get("https://serpapi.com/search", params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()

            # Extract the first restaurant result
            restaurants = search_data.get("results", [])
            if not restaurants:
                logger.warning(f"No restaurants found for: {restaurant_name} in {location}")
                return None

            restaurant = restaurants[0]
            place_id = restaurant.get("place_id")
            domain = restaurant.get("domain")

            if not place_id and not domain:
                logger.warning(f"No place_id or domain found for restaurant: {restaurant_name}")
                return None

            # Now fetch reviews for this restaurant
            reviews_params = {
                "api_key": self.api_key,
                "engine": "opentable_reviews",
                "place_id": place_id,
                "open_table_domain": domain,
                "page": 1,  # Start with first page
            }

            reviews_response = await client.get("https://serpapi.com/search", params=reviews_params)
            reviews_response.raise_for_status()
            reviews_data = reviews_response.json()

            return reviews_data

    def _format_restaurant_summary(self, reviews_data: Dict[str, Any]) -> str:
        """
        Format restaurant summary information.

        Args:
            reviews_data: Reviews data from API

        Returns:
            Formatted summary string
        """
        summary = reviews_data.get("reviews_summary", {})
        ratings = summary.get("ratings_summary", {})

        overall = ratings.get("overall", 0)
        reviews_count = summary.get("reviews_count", 0)
        food = ratings.get("food", 0)
        service = ratings.get("service", 0)
        ambience = ratings.get("ambience", 0)

        summary_text = f"Overall: {overall}/5 from {reviews_count} reviews"
        if food > 0:
            summary_text += f" | Food: {food}/5"
        if service > 0:
            summary_text += f" | Service: {service}/5"
        if ambience > 0:
            summary_text += f" | Ambience: {ambience}/5"

        noise = ratings.get("noise", "")
        if noise:
            summary_text += f" | Noise: {noise}"

        ai_summary = summary.get("ai_summary", "")
        if ai_summary:
            summary_text += f" | {ai_summary}"

        return summary_text

    def _format_review_summary(self, review: Dict[str, Any], restaurant_name: str) -> str:
        """
        Format individual review information.

        Args:
            review: Individual review data
            restaurant_name: Name of the restaurant

        Returns:
            Formatted review summary string
        """
        content = review.get("content", "").strip()
        rating = review.get("rating", {}).get("overall", 0)
        user = review.get("user", {})
        reviewer_name = user.get("name", "Anonymous")
        location = user.get("location", "")

        # Truncate content if too long
        if len(content) > 200:
            content = content[:200] + "..."

        summary = f"{reviewer_name}"
        if location:
            summary += f" ({location})"
        summary += f" gave {rating}/5 stars"

        if content:
            summary += f": \"{content}\""

        # Add highlights from ratings
        highlights = []
        ratings = review.get("rating", {})
        if ratings.get("food", 0) >= 4:
            highlights.append("excellent food")
        if ratings.get("service", 0) >= 4:
            highlights.append("great service")
        if ratings.get("ambience", 0) >= 4:
            highlights.append("wonderful ambience")

        if highlights:
            summary += f" (Highlights: {', '.join(highlights)})"

        return summary

    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> ConnectorResult:
        """
        Main connector interface - fetch dining information based on user preferences.

        Args:
            since: Timestamp to search from
            limit: Maximum number of results
            **kwargs: Should include user_preferences

        Returns:
            ConnectorResult with dining information
        """
        user_preferences = kwargs.get('user_preferences', {})
        favorite_restaurants = user_preferences.get('favorite_restaurants', [])

        if not favorite_restaurants:
            logger.info("No favorite restaurants specified for dining review search, skipping")
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="ok",
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )

        all_reviews = []

        # Search for reviews of favorite restaurants
        for restaurant in favorite_restaurants[:3]:  # Limit to 3 restaurants to avoid rate limits
            try:
                name = restaurant.get('name', '')
                location = restaurant.get('location', 'New York')

                if name:
                    restaurant_reviews = await self.search_restaurant_reviews(
                        name, location, limit or 3
                    )
                    all_reviews.extend(restaurant_reviews)

            except Exception as e:
                logger.error(f"Error fetching reviews for restaurant {restaurant}: {e}")
                continue

        # Convert BriefItem objects to dicts for ConnectorResult
        items = []
        for item in all_reviews:
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