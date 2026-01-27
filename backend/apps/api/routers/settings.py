"""Settings endpoints"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from packages.database import get_db, crud
from packages.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_SETTINGS = {
    "topics": ["AI", "technology", "startups"],
    "vip_people": [],
    "projects": [],
    "enabled_modules": ["gmail", "calendar", "tasks", "keep", "news", "research", "flights", "dining", "travel", "local", "shopping"],
    "upcoming_trips": [
        {
            "departure_airport": "LAX",
            "arrival_airport": "AUS",
            "departure_date": "2026-02-15",
            "return_date": "2026-02-20"
        }
    ],
    "favorite_restaurants": [
        {
            "name": "Le Bernardin",
            "location": "New York"
        }
    ],
    "travel_interests": ["luxury hotels", "attractions"],
    "upcoming_destinations": [
        {
            "name": "Central Park",
            "location": "New York",
            "type": "ATTRACTION"
        }
    ],
    "local_interests": ["coffee shops", "bookstores"],
    "local_services_needed": [
        {
            "service_type": "plumbers",
            "location": "New York"
        }
    ],
    "shopping_interests": ["wireless headphones", "coffee makers"],
    "products_to_track": [
        {
            "name": "iPhone 15",
            "category": "aps"
        }
    ],
}


@router.get("/{user_id}")
async def get_user_settings(
    user_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user settings"""
    # Validate user_id format (reuse from brief.py)
    import re
    USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
    if not USER_ID_PATTERN.match(user_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id format. Must be 1-64 alphanumeric characters, underscores, or hyphens."
        )

    # Get or create user
    user = crud.get_or_create_user(db, user_id=user_id)

    # Return user settings or defaults
    settings = user.settings_json or DEFAULT_SETTINGS
    return settings


@router.put("/{user_id}")
async def update_user_settings(
    user_id: str,
    settings: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update user settings"""
    # Validate user_id format
    import re
    USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
    if not USER_ID_PATTERN.match(user_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id format. Must be 1-64 alphanumeric characters, underscores, or hyphens."
        )

    # Get or create user
    user = crud.get_or_create_user(db, user_id=user_id)

    # Validate settings structure
    required_keys = ["topics", "vip_people", "projects", "enabled_modules", "upcoming_trips", "favorite_restaurants", "travel_interests", "upcoming_destinations", "local_interests", "local_services_needed", "shopping_interests", "products_to_track"]
    if not all(key in settings for key in required_keys):
        raise HTTPException(
            status_code=400,
            detail=f"Settings must contain all required keys: {required_keys}"
        )

    # Validate types
    if not isinstance(settings["topics"], list) or not all(isinstance(t, str) for t in settings["topics"]):
        raise HTTPException(status_code=400, detail="topics must be a list of strings")

    if not isinstance(settings["vip_people"], list) or not all(isinstance(v, str) for v in settings["vip_people"]):
        raise HTTPException(status_code=400, detail="vip_people must be a list of strings")

    if not isinstance(settings["projects"], list) or not all(isinstance(p, str) for p in settings["projects"]):
        raise HTTPException(status_code=400, detail="projects must be a list of strings")

    if not isinstance(settings["enabled_modules"], list) or not all(isinstance(m, str) for m in settings["enabled_modules"]):
        raise HTTPException(status_code=400, detail="enabled_modules must be a list of strings")

    if not isinstance(settings["upcoming_trips"], list):
        raise HTTPException(status_code=400, detail="upcoming_trips must be a list")

    # Validate upcoming_trips structure
    for i, trip in enumerate(settings["upcoming_trips"]):
        if not isinstance(trip, dict):
            raise HTTPException(status_code=400, detail=f"upcoming_trips[{i}] must be an object")
        required_trip_keys = ["departure_airport", "arrival_airport", "departure_date"]
        if not all(key in trip for key in required_trip_keys):
            raise HTTPException(status_code=400, detail=f"upcoming_trips[{i}] must contain {required_trip_keys}")

    if not isinstance(settings["favorite_restaurants"], list):
        raise HTTPException(status_code=400, detail="favorite_restaurants must be a list")

    # Validate favorite_restaurants structure
    for i, restaurant in enumerate(settings["favorite_restaurants"]):
        if not isinstance(restaurant, dict):
            raise HTTPException(status_code=400, detail=f"favorite_restaurants[{i}] must be an object")
        required_restaurant_keys = ["name", "location"]
        if not all(key in restaurant for key in required_restaurant_keys):
            raise HTTPException(status_code=400, detail=f"favorite_restaurants[{i}] must contain {required_restaurant_keys}")

    if not isinstance(settings["travel_interests"], list) or not all(isinstance(i, str) for i in settings["travel_interests"]):
        raise HTTPException(status_code=400, detail="travel_interests must be a list of strings")

    if not isinstance(settings["upcoming_destinations"], list):
        raise HTTPException(status_code=400, detail="upcoming_destinations must be a list")

    # Validate upcoming_destinations structure
    for i, destination in enumerate(settings["upcoming_destinations"]):
        if not isinstance(destination, dict):
            raise HTTPException(status_code=400, detail=f"upcoming_destinations[{i}] must be an object")
        required_destination_keys = ["name", "location", "type"]
        if not all(key in destination for key in required_destination_keys):
            raise HTTPException(status_code=400, detail=f"upcoming_destinations[{i}] must contain {required_destination_keys}")

    if not isinstance(settings["local_interests"], list) or not all(isinstance(i, str) for i in settings["local_interests"]):
        raise HTTPException(status_code=400, detail="local_interests must be a list of strings")

    if not isinstance(settings["local_services_needed"], list):
        raise HTTPException(status_code=400, detail="local_services_needed must be a list")

    # Validate local_services_needed structure
    for i, service in enumerate(settings["local_services_needed"]):
        if not isinstance(service, dict):
            raise HTTPException(status_code=400, detail=f"local_services_needed[{i}] must be an object")
        required_service_keys = ["service_type", "location"]
        if not all(key in service for key in required_service_keys):
            raise HTTPException(status_code=400, detail=f"local_services_needed[{i}] must contain {required_service_keys}")

    if not isinstance(settings["shopping_interests"], list) or not all(isinstance(i, str) for i in settings["shopping_interests"]):
        raise HTTPException(status_code=400, detail="shopping_interests must be a list of strings")

    if not isinstance(settings["products_to_track"], list):
        raise HTTPException(status_code=400, detail="products_to_track must be a list")

    # Validate products_to_track structure
    for i, product in enumerate(settings["products_to_track"]):
        if not isinstance(product, dict):
            raise HTTPException(status_code=400, detail=f"products_to_track[{i}] must be an object")
        required_product_keys = ["name"]
        if not all(key in product for key in required_product_keys):
            raise HTTPException(status_code=400, detail=f"products_to_track[{i}] must contain {required_product_keys}")

    # Update user settings
    user.settings_json = settings
    db.commit()

    logger.info(f"Updated settings for user {user_id}")
    return {"message": "Settings updated successfully", "settings": settings}