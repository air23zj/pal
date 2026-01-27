"""
Shopping connector using SerpApi Amazon Search API.

Provides product recommendations and shopping insights.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import httpx

from .base import BaseConnector, ConnectorResult
from packages.shared.schemas import BriefItem, Entity

logger = logging.getLogger(__name__)


class ShoppingConnector(BaseConnector):
    """
    Amazon Search connector using SerpApi.

    Searches for products, prices, and shopping recommendations on Amazon.
    """

    @property
    def source_name(self) -> str:
        """Return the name of this connector's source"""
        return "shopping"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpApi Amazon Search connector.

        Args:
            api_key: SerpApi API key (defaults to SERPAPI_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("No SerpApi key provided - shopping searches will be disabled")

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

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        max_results: int = 5
    ) -> List[BriefItem]:
        """
        Search for products on Amazon.

        Args:
            query: Search query (e.g., "wireless headphones", "coffee makers")
            category: Amazon category filter (optional)
            max_results: Maximum number of product results to return

        Returns:
            List of BriefItem objects with product information
        """
        if not self.is_available():
            logger.info("SerpApi not configured, skipping product search")
            return []

        results = []

        try:
            logger.info(f"Searching Amazon for: {query}")

            products_data = await self._search_amazon(
                query, category, max_results
            )

            for product in products_data[:max_results]:
                # Create BriefItem for each product
                brief_item = BriefItem(
                    item_ref=f"shopping_{product.get('product_id', '')}_{hash(str(product))}",
                    source="shopping",
                    type="product",
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    title=f"{product.get('title', 'Unknown Product')} - Amazon",
                    summary=self._format_product_summary(product),
                    why_it_matters="pending",  # Will be filled by LLM synthesizer
                    entities=[
                        Entity(kind="product", key=product.get('title', '')),
                        Entity(kind="brand", key=product.get('brand', '')),
                    ],
                    novelty={"label": "NEW", "reason": "product_search", "first_seen_utc": datetime.now(timezone.utc).isoformat()},
                    ranking={
                        "relevance_score": 0.9,  # Product recommendations are highly relevant
                        "urgency_score": 0.5,    # Shopping has moderate urgency
                        "credibility_score": 0.8,  # Amazon reviews are user-generated
                        "impact_score": 0.7,      # Shopping decisions have moderate impact
                        "actionability_score": 0.8, # Can lead to purchases
                        "final_score": 0.7
                    },
                    evidence=[],
                    suggested_actions=[]
                )

                # Add product metadata
                brief_item.metadata = {
                    "product_id": product.get("product_id", ""),
                    "title": product.get("title", ""),
                    "brand": product.get("brand", ""),
                    "price": product.get("price", 0),
                    "original_price": product.get("original_price", 0),
                    "currency": product.get("currency", "USD"),
                    "rating": product.get("rating", 0),
                    "reviews_count": product.get("reviews_count", 0),
                    "availability": product.get("availability", ""),
                    "thumbnail": product.get("thumbnail", ""),
                    "link": product.get("link", ""),
                    "search_query": query,
                    "category": category,
                }

                results.append(brief_item)

        except Exception as e:
            logger.error(f"Error searching Amazon for {query}: {e}")
            return []

        logger.info(f"Found {len(results)} products for {query}")
        return results

    async def _search_amazon(
        self,
        query: str,
        category: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search Amazon using SerpApi.

        Args:
            query: Search query
            category: Amazon category filter
            max_results: Maximum results to return

        Returns:
            List of product information from Amazon
        """
        if not self.api_key:
            raise ValueError("SerpApi key not configured")

        params = {
            "api_key": self.api_key,
            "engine": "amazon",
            "q": query,
            "device": "desktop",
            "language": "en_US",
        }

        if category:
            params["i"] = category  # Amazon category filter

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://serpapi.com/search", params=params)
            response.raise_for_status()

            data = response.json()

            # Extract organic results (main product listings)
            products = data.get("organic_results", [])
            return products

    def _format_product_summary(self, product: Dict[str, Any]) -> str:
        """
        Format product information into a readable summary.

        Args:
            product: Product data from Amazon API

        Returns:
            Formatted summary string
        """
        title = product.get("title", "Unknown Product")
        brand = product.get("brand", "")
        price = product.get("price", 0)
        original_price = product.get("original_price", 0)
        currency = product.get("currency", "USD")
        rating = product.get("rating", 0)
        reviews_count = product.get("reviews_count", 0)
        availability = product.get("availability", "")

        summary = title

        if brand:
            summary += f" by {brand}"

        if price > 0:
            summary += f" - {currency}{price}"
            if original_price and original_price > price:
                discount = ((original_price - price) / original_price) * 100
                summary += f" (was {currency}{original_price}, {discount:.0f}% off)"

        if rating > 0:
            summary += f" - {rating}/5 stars"

        if reviews_count > 0:
            summary += f" from {reviews_count} reviews"

        if availability and "out of stock" in availability.lower():
            summary += f" - {availability}"

        return summary

    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> ConnectorResult:
        """
        Main connector interface - fetch shopping information based on user preferences.

        Args:
            since: Timestamp to search from
            limit: Maximum number of results
            **kwargs: Should include user_preferences

        Returns:
            ConnectorResult with shopping information
        """
        user_preferences = kwargs.get('user_preferences', {})
        shopping_interests = user_preferences.get('shopping_interests', [])
        products_to_track = user_preferences.get('products_to_track', [])

        if not shopping_interests and not products_to_track:
            logger.info("No shopping interests or products to track specified for shopping search, skipping")
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="ok",
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )

        all_products = []

        # Search for products based on shopping interests
        for interest in shopping_interests[:2]:  # Limit to avoid rate limits
            try:
                interest_results = await self.search_products(
                    interest, None, limit or 3
                )
                all_products.extend(interest_results)
            except Exception as e:
                logger.error(f"Error fetching products for interest {interest}: {e}")
                continue

        # Search for specific products to track
        for product in products_to_track[:2]:  # Limit to avoid rate limits
            try:
                product_name = product.get('name', '')
                product_category = product.get('category', None)

                if product_name:
                    product_results = await self.search_products(
                        product_name, product_category, limit or 3
                    )
                    all_products.extend(product_results)
            except Exception as e:
                logger.error(f"Error fetching products for tracking {product}: {e}")
                continue

        # Convert BriefItem objects to dicts for ConnectorResult
        items = []
        for item in all_products:
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