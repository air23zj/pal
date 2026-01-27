from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Union
from enum import Enum

class WeatherAlert(BaseModel):
    type: str
    severity: str
    description: str
    start_time: datetime
    end_time: datetime

class AirQuality(BaseModel):
    aqi: int = Field(..., ge=0, le=500)
    co: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    pm2_5: Optional[float] = None
    pm10: Optional[float] = None
    so2: Optional[float] = None

class HourlyForecast(BaseModel):
    timestamp: datetime
    temperature: float
    feels_like: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: float
    description: str
    icon: str
    precipitation_probability: Optional[float] = None
    precipitation: Optional[float] = None

class DailyForecast(BaseModel):
    date: datetime
    temp_min: float
    temp_max: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: float
    description: str
    icon: str
    precipitation_probability: Optional[float] = None
    precipitation: Optional[float] = None
    uv_index: Optional[float] = None

class Forecast(BaseModel):
    hourly: List[HourlyForecast]
    daily: List[DailyForecast]

class UserLocationBase(BaseModel):
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    is_primary: bool = Field(default=False)

class UserLocationCreate(UserLocationBase):
    pass

class UserLocationUpdate(BaseModel):
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_primary: Optional[bool] = None

class UserLocation(UserLocationBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WeatherDataBase(BaseModel):
    temperature: float
    feels_like: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: float
    description: str
    icon: str
    precipitation: Optional[float] = None
    cloud_cover: float
    uv_index: Optional[float] = None
    air_quality: Optional[AirQuality] = None
    forecast: Optional[Forecast] = None
    alerts: Optional[List[WeatherAlert]] = None

class WeatherData(WeatherDataBase):
    id: int
    location_id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class WeatherResponse(BaseModel):
    location: UserLocation
    current: WeatherData

class WeatherSummary(BaseModel):
    temperature: float
    description: str
    icon: str
    alerts_count: int = 0

class LocationWeatherSummary(BaseModel):
    location: UserLocation
    weather: WeatherSummary 