from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..core.database import Base

class UserLocation(Base):
    __tablename__ = "user_locations"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    city = Column(String)
    country = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="locations")
    weather_data = relationship("WeatherData", back_populates="location")

class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("user_locations.id"))
    temperature = Column(Float)  # in Celsius
    feels_like = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    description = Column(String)
    icon = Column(String)
    precipitation = Column(Float, nullable=True)
    cloud_cover = Column(Float)
    uv_index = Column(Float, nullable=True)
    air_quality = Column(JSON, nullable=True)  # Store detailed air quality data
    forecast = Column(JSON, nullable=True)  # Store hourly/daily forecast data
    alerts = Column(JSON, nullable=True)  # Store weather alerts/warnings
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    location = relationship("UserLocation", back_populates="weather_data") 