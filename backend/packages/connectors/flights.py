"""
Flights connector using SerpApi Google Flights API.

Provides flight search and travel information for upcoming trips.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import httpx

from .base import BaseConnector, ConnectorResult
from packages.shared.schemas import BriefItem, Entity

logger = logging.getLogger(__name__)


class FlightsConnector(BaseConnector):
    """
    Google Flights connector using SerpApi.

    Searches for flight information and provides travel insights.
    """

    @property
    def source_name(self) -> str:
        """Return the name of this connector's source"""
        return "flights"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpApi Google Flights connector.

        Args:
            api_key: SerpApi API key (defaults to SERPAPI_API_KEY env var)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("No SerpApi key provided - flight searches will be disabled")

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

    async def search_flights(
        self,
        departure_id: str,
        arrival_id: str,
        departure_date: str,
        return_date: Optional[str] = None,
        max_results: int = 5
    ) -> List[BriefItem]:
        """
        Search for flights between two airports.

        Args:
            departure_id: Departure airport code (e.g., "LAX")
            arrival_id: Arrival airport code (e.g., "AUS")
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (optional)
            max_results: Maximum number of flight results to return

        Returns:
            List of BriefItem objects with flight information
        """
        if not self.is_available():
            logger.info("SerpApi not configured, skipping flight search")
            return []

        results = []

        try:
            logger.info(f"Searching flights: {departure_id} to {arrival_id} on {departure_date}")

            flights_data = await self._search_google_flights(
                departure_id, arrival_id, departure_date, return_date, max_results
            )

            for flight_info in flights_data:
                # Create BriefItem for each flight option
                brief_item = BriefItem(
                    item_ref=f"flight_{departure_id}_{arrival_id}_{hash(str(flight_info))}",
                    source="flights",
                    type="flight",
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    title=f"Flight {departure_id} to {arrival_id}",
                    summary=self._format_flight_summary(flight_info),
                    why_it_matters="pending",  # Will be filled by LLM synthesizer
                    entities=[
                        Entity(kind="location", key=departure_id),
                        Entity(kind="location", key=arrival_id),
                        Entity(kind="airline", key=flight_info.get("airline", "")),
                    ],
                    novelty={"label": "NEW", "reason": "flight_search", "first_seen_utc": datetime.now(timezone.utc).isoformat()},
                    ranking={
                        "relevance_score": 0.9,  # Flights are highly relevant for travel planning
                        "urgency_score": self._calculate_flight_urgency(flight_info, departure_date),
                        "credibility_score": 0.9,  # Google Flights data is reliable
                        "impact_score": 0.8,      # Travel planning has high impact
                        "actionability_score": 0.7, # Can lead to booking actions
                        "final_score": 0.8
                    },
                    evidence=[],
                    suggested_actions=[]
                )

                # Add flight-specific metadata
                brief_item.metadata = {
                    "departure_airport": departure_id,
                    "arrival_airport": arrival_id,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "price": flight_info.get("price", 0),
                    "airline": flight_info.get("airline", ""),
                    "flight_number": flight_info.get("flight_number", ""),
                    "duration": flight_info.get("duration", 0),
                    "stops": len(flight_info.get("layovers", [])),
                    "carbon_emissions": flight_info.get("carbon_emissions", {}),
                    "booking_token": flight_info.get("booking_token", ""),
                }

                results.append(brief_item)

        except Exception as e:
            logger.error(f"Error searching flights {departure_id} to {arrival_id}: {e}")
            return []

        logger.info(f"Found {len(results)} flight options")
        return results

    async def _search_google_flights(
        self,
        departure_id: str,
        arrival_id: str,
        departure_date: str,
        return_date: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search Google Flights using SerpApi.

        Args:
            departure_id: Departure airport code
            arrival_id: Arrival airport code
            departure_date: Departure date
            return_date: Return date (optional)
            max_results: Maximum results to return

        Returns:
            List of flight information dictionaries
        """
        if not self.api_key:
            raise ValueError("SerpApi key not configured")

        params = {
            "api_key": self.api_key,
            "engine": "google_flights",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": departure_date,
            "type": "2" if return_date else "1",  # 1 = one-way, 2 = round-trip
            "currency": "USD",
            "hl": "en",
        }

        if return_date:
            params["return_date"] = return_date

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://serpapi.com/search", params=params)
            response.raise_for_status()

            data = response.json()

            # Extract flight results
            results = []
            flights_data = data.get("best_flights", []) + data.get("other_flights", [])

            for flight_option in flights_data[:max_results]:
                # Extract key flight information
                flights = flight_option.get("flights", [])
                if flights:
                    first_flight = flights[0]
                    results.append({
                        "airline": first_flight.get("airline", ""),
                        "flight_number": first_flight.get("flight_number", ""),
                        "departure_airport": first_flight.get("departure_airport", {}).get("id", ""),
                        "arrival_airport": first_flight.get("arrival_airport", {}).get("id", ""),
                        "duration": flight_option.get("total_duration", 0),
                        "price": flight_option.get("price", 0),
                        "layovers": flight_option.get("layovers", []),
                        "carbon_emissions": flight_option.get("carbon_emissions", {}),
                        "booking_token": flight_option.get("booking_token", ""),
                        "type": flight_option.get("type", "One way"),
                    })

            return results

    def _format_flight_summary(self, flight_info: Dict[str, Any]) -> str:
        """
        Format flight information into a readable summary.

        Args:
            flight_info: Flight data from API

        Returns:
            Formatted summary string
        """
        airline = flight_info.get("airline", "Unknown Airline")
        flight_number = flight_info.get("flight_number", "")
        price = flight_info.get("price", 0)
        duration = flight_info.get("duration", 0)
        stops = len(flight_info.get("layovers", []))

        # Format duration
        hours = duration // 60
        minutes = duration % 60
        duration_str = f"{hours}h {minutes}m"

        # Format stops
        if stops == 0:
            stops_str = "direct"
        elif stops == 1:
            stops_str = "1 stop"
        else:
            stops_str = f"{stops} stops"

        summary = f"{airline} {flight_number}: ${price}, {duration_str}, {stops_str}"

        # Add carbon emissions info if available
        emissions = flight_info.get("carbon_emissions", {})
        if emissions.get("this_flight"):
            co2_kg = emissions["this_flight"] // 1000  # Convert grams to kg
            summary += f", ~{co2_kg}kg CO2"

        return summary

    def _calculate_flight_urgency(self, flight_info: Dict[str, Any], departure_date: str) -> float:
        """
        Calculate urgency score based on flight timing and price.

        Args:
            flight_info: Flight data
            departure_date: Departure date string

        Returns:
            Urgency score between 0.0 and 1.0
        """
        try:
            # Parse departure date
            dep_date = datetime.fromisoformat(departure_date)
            now = datetime.now(timezone.utc)

            # Calculate days until departure
            days_until = (dep_date - now).days

            if days_until < 0:
                return 0.0  # Past flights
            elif days_until <= 1:
                return 1.0  # Very urgent (departing soon)
            elif days_until <= 7:
                return 0.8  # Urgent (departing this week)
            elif days_until <= 30:
                return 0.6  # Moderately urgent
            else:
                return 0.3  # Not urgent

        except Exception:
            return 0.5  # Default urgency

    async def fetch(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> ConnectorResult:
        """
        Main connector interface - fetch flight information based on user preferences.

        Args:
            since: Timestamp to search from
            limit: Maximum number of results
            **kwargs: Should include user_preferences

        Returns:
            ConnectorResult with flight information
        """
        user_preferences = kwargs.get('user_preferences', {})
        trips = user_preferences.get('upcoming_trips', [])

        if not trips:
            logger.info("No upcoming trips specified for flight search, skipping")
            return ConnectorResult(
                source=self.source_name,
                items=[],
                status="ok",
                fetched_at=datetime.now(timezone.utc),
                since_timestamp=since,
            )

        all_flights = []

        # Search for flights for each upcoming trip
        for trip in trips[:2]:  # Limit to 2 trips to avoid rate limits
            try:
                departure = trip.get('departure_airport')
                arrival = trip.get('arrival_airport')
                departure_date = trip.get('departure_date')
                return_date = trip.get('return_date')

                if departure and arrival and departure_date:
                    trip_flights = await self.search_flights(
                        departure, arrival, departure_date, return_date, limit or 3
                    )
                    all_flights.extend(trip_flights)

            except Exception as e:
                logger.error(f"Error fetching flights for trip {trip}: {e}")
                continue

        # Convert BriefItem objects to dicts for ConnectorResult
        items = []
        for item in all_flights:
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