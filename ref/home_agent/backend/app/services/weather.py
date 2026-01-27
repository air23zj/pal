from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
import httpx
import json
from fastapi import HTTPException

from ..models.weather import UserLocation, WeatherData
from ..schemas.weather import (
    UserLocationCreate,
    UserLocationUpdate,
    WeatherResponse,
    WeatherSummary,
    LocationWeatherSummary,
    AirQuality,
    WeatherAlert,
    Forecast
)
from ..core.config import settings

class WeatherService:
    WEATHER_API_BASE_URL = "https://api.openweathermap.org/data/3.0"
    GEOCODING_API_BASE_URL = "https://api.openweathermap.org/geo/1.0"

    @staticmethod
    async def get_location_coordinates(city: str, country: str) -> Dict[str, float]:
        """Get coordinates for a city using OpenWeatherMap Geocoding API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WeatherService.GEOCODING_API_BASE_URL}/direct",
                params={
                    "q": f"{city},{country}",
                    "limit": 1,
                    "appid": settings.OPENWEATHER_API_KEY
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to get location coordinates")
            
            data = response.json()
            if not data:
                raise HTTPException(status_code=404, detail="Location not found")
            
            return {
                "latitude": data[0]["lat"],
                "longitude": data[0]["lon"]
            }

    @staticmethod
    async def fetch_weather_data(latitude: float, longitude: float) -> Dict[str, Any]:
        """Fetch weather data from OpenWeatherMap API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WeatherService.WEATHER_API_BASE_URL}/onecall",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "metric",
                    "exclude": "minutely"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch weather data")
            
            return response.json()

    @staticmethod
    def create_location(
        db: Session, user_id: int, location: UserLocationCreate
    ) -> UserLocation:
        # If this is the first location or marked as primary, update other locations
        if location.is_primary:
            existing_primary = db.query(UserLocation)\
                .filter(
                    UserLocation.owner_id == user_id,
                    UserLocation.is_primary == True
                )\
                .first()
            if existing_primary:
                existing_primary.is_primary = False

        db_location = UserLocation(**location.model_dump(), owner_id=user_id)
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        return db_location

    @staticmethod
    def get_locations(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[UserLocation]:
        return db.query(UserLocation)\
            .filter(UserLocation.owner_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_location(
        db: Session, user_id: int, location_id: int
    ) -> Optional[UserLocation]:
        return db.query(UserLocation)\
            .filter(
                UserLocation.owner_id == user_id,
                UserLocation.id == location_id
            )\
            .first()

    @staticmethod
    def update_location(
        db: Session, user_id: int, location_id: int, location: UserLocationUpdate
    ) -> Optional[UserLocation]:
        db_location = WeatherService.get_location(db, user_id, location_id)
        if db_location:
            update_data = location.model_dump(exclude_unset=True)
            
            # Handle primary location updates
            if "is_primary" in update_data and update_data["is_primary"]:
                existing_primary = db.query(UserLocation)\
                    .filter(
                        UserLocation.owner_id == user_id,
                        UserLocation.is_primary == True,
                        UserLocation.id != location_id
                    )\
                    .first()
                if existing_primary:
                    existing_primary.is_primary = False

            for field, value in update_data.items():
                setattr(db_location, field, value)
            
            db.commit()
            db.refresh(db_location)
        return db_location

    @staticmethod
    def delete_location(
        db: Session, user_id: int, location_id: int
    ) -> bool:
        db_location = WeatherService.get_location(db, user_id, location_id)
        if db_location:
            db.delete(db_location)
            db.commit()
            return True
        return False

    @staticmethod
    def save_weather_data(
        db: Session, location_id: int, weather_data: Dict[str, Any]
    ) -> WeatherData:
        """Save weather data to database"""
        current = weather_data["current"]
        
        db_weather = WeatherData(
            location_id=location_id,
            temperature=current["temp"],
            feels_like=current["feels_like"],
            humidity=current["humidity"],
            pressure=current["pressure"],
            wind_speed=current["wind_speed"],
            wind_direction=current["wind_deg"],
            description=current["weather"][0]["description"],
            icon=current["weather"][0]["icon"],
            cloud_cover=current["clouds"],
            uv_index=current.get("uvi"),
            air_quality=weather_data.get("air_quality"),
            forecast=json.dumps({
                "hourly": weather_data["hourly"],
                "daily": weather_data["daily"]
            }),
            alerts=json.dumps(weather_data.get("alerts", [])),
            timestamp=datetime.fromtimestamp(current["dt"])
        )
        
        db.add(db_weather)
        db.commit()
        db.refresh(db_weather)
        return db_weather

    @staticmethod
    def get_latest_weather(
        db: Session, location_id: int
    ) -> Optional[WeatherData]:
        """Get latest weather data for a location"""
        return db.query(WeatherData)\
            .filter(WeatherData.location_id == location_id)\
            .order_by(desc(WeatherData.timestamp))\
            .first()

    @staticmethod
    async def get_weather_for_location(
        db: Session, user_id: int, location_id: int, force_refresh: bool = False
    ) -> WeatherResponse:
        """Get weather data for a specific location"""
        location = WeatherService.get_location(db, user_id, location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        latest_weather = WeatherService.get_latest_weather(db, location_id)
        
        # Refresh if no data or data is old or force refresh requested
        if (
            force_refresh or
            not latest_weather or
            datetime.utcnow() - latest_weather.timestamp > timedelta(hours=1)
        ):
            weather_data = await WeatherService.fetch_weather_data(
                location.latitude,
                location.longitude
            )
            latest_weather = WeatherService.save_weather_data(
                db, location_id, weather_data
            )

        return WeatherResponse(location=location, current=latest_weather)

    @staticmethod
    async def get_weather_summaries(
        db: Session, user_id: int
    ) -> List[LocationWeatherSummary]:
        """Get weather summaries for all user locations"""
        locations = WeatherService.get_locations(db, user_id)
        summaries = []

        for location in locations:
            latest_weather = WeatherService.get_latest_weather(db, location.id)
            
            if latest_weather:
                alerts = json.loads(latest_weather.alerts) if latest_weather.alerts else []
                summary = WeatherSummary(
                    temperature=latest_weather.temperature,
                    description=latest_weather.description,
                    icon=latest_weather.icon,
                    alerts_count=len(alerts)
                )
                summaries.append(LocationWeatherSummary(
                    location=location,
                    weather=summary
                ))

        return summaries 