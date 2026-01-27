from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....services.weather import WeatherService
from ....schemas.weather import (
    UserLocation,
    UserLocationCreate,
    UserLocationUpdate,
    WeatherResponse,
    LocationWeatherSummary
)
from ...dependencies.auth import get_current_user
from ....schemas.user import User

router = APIRouter()

@router.post("/locations/", response_model=UserLocation)
async def create_location(
    *,
    location_in: UserLocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new location for weather tracking.
    """
    # Get coordinates if not provided
    if not all([location_in.latitude, location_in.longitude]):
        coords = await WeatherService.get_location_coordinates(
            location_in.city,
            location_in.country
        )
        location_in.latitude = coords["latitude"]
        location_in.longitude = coords["longitude"]

    location = WeatherService.create_location(db, current_user.id, location_in)
    return location

@router.get("/locations/", response_model=List[UserLocation])
def get_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve all locations for the current user.
    """
    locations = WeatherService.get_locations(db, current_user.id, skip, limit)
    return locations

@router.get("/locations/{location_id}", response_model=UserLocation)
def get_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific location by ID.
    """
    location = WeatherService.get_location(db, current_user.id, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.put("/locations/{location_id}", response_model=UserLocation)
async def update_location(
    *,
    location_id: int,
    location_in: UserLocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update a location.
    """
    # Get coordinates if city or country is updated
    if location_in.city and location_in.country:
        coords = await WeatherService.get_location_coordinates(
            location_in.city,
            location_in.country
        )
        location_in.latitude = coords["latitude"]
        location_in.longitude = coords["longitude"]

    location = WeatherService.update_location(
        db, current_user.id, location_id, location_in
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.delete("/locations/{location_id}")
def delete_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete a location.
    """
    success = WeatherService.delete_location(db, current_user.id, location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"message": "Location successfully deleted"}

@router.get("/locations/{location_id}/weather", response_model=WeatherResponse)
async def get_location_weather(
    location_id: int,
    force_refresh: bool = Query(False, description="Force refresh weather data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get weather data for a specific location.
    """
    return await WeatherService.get_weather_for_location(
        db, current_user.id, location_id, force_refresh
    )

@router.get("/summary", response_model=List[LocationWeatherSummary])
async def get_weather_summaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get weather summaries for all user locations.
    """
    return await WeatherService.get_weather_summaries(db, current_user.id) 