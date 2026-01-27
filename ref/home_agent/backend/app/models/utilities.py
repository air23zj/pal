from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from app.db.base_class import Base

class CalculationType(str, Enum):
    FINANCIAL = "financial"
    SCIENTIFIC = "scientific"
    UNIT_CONVERSION = "unit_conversion"
    CURRENCY_CONVERSION = "currency_conversion"
    TIME_ZONE_CONVERSION = "time_zone_conversion"

class CalculationHistory(Base):
    __tablename__ = "calculation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(SQLEnum(CalculationType), nullable=False)
    input_data = Column(JSON, nullable=False)  # Store input parameters
    result = Column(JSON, nullable=False)  # Store calculation result
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="calculation_history")

class UnitConversionPreference(Base):
    __tablename__ = "unit_conversion_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    default_length_unit = Column(String(20), default="meters")
    default_weight_unit = Column(String(20), default="kilograms")
    default_temperature_unit = Column(String(20), default="celsius")
    default_volume_unit = Column(String(20), default="liters")
    default_speed_unit = Column(String(20), default="kmh")
    default_area_unit = Column(String(20), default="square_meters")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="unit_conversion_preferences")

class CurrencyPreference(Base):
    __tablename__ = "currency_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    default_from_currency = Column(String(3), default="USD")
    default_to_currency = Column(String(3), default="EUR")
    watched_currencies = Column(JSON, nullable=True)  # List of currency codes to watch
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="currency_preferences")

class TimeZonePreference(Base):
    __tablename__ = "timezone_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    default_timezone = Column(String(50), default="UTC")
    watched_timezones = Column(JSON, nullable=True)  # List of timezone identifiers
    time_format = Column(String(20), default="24h")  # 12h or 24h
    date_format = Column(String(20), default="YYYY-MM-DD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="timezone_preferences")

class GeneratedContent(Base):
    __tablename__ = "generated_content"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_type = Column(String(50), nullable=False)  # password, qr_code, etc.
    content = Column(String, nullable=False)  # Generated content or file path
    metadata = Column(JSON, nullable=True)  # Additional metadata
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="generated_content")

class FileConversion(Base):
    __tablename__ = "file_conversions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_file = Column(String, nullable=False)  # Original file path or URL
    converted_file = Column(String, nullable=False)  # Converted file path
    source_format = Column(String(20), nullable=False)
    target_format = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")  # pending, completed, failed
    error_message = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional conversion metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="file_conversions") 