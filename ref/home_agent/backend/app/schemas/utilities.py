from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, constr
from enum import Enum

from app.models.utilities import CalculationType

# Enums
class TimeFormat(str, Enum):
    H12 = "12h"
    H24 = "24h"

class DateFormat(str, Enum):
    ISO = "YYYY-MM-DD"
    US = "MM/DD/YYYY"
    EU = "DD/MM/YYYY"
    CUSTOM = "custom"

class ConversionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

# Base schemas
class CalculationBase(BaseModel):
    type: CalculationType
    input_data: Dict[str, Any]

class UnitConversionPreferenceBase(BaseModel):
    default_length_unit: str = "meters"
    default_weight_unit: str = "kilograms"
    default_temperature_unit: str = "celsius"
    default_volume_unit: str = "liters"
    default_speed_unit: str = "kmh"
    default_area_unit: str = "square_meters"

class CurrencyPreferenceBase(BaseModel):
    default_from_currency: constr(regex="^[A-Z]{3}$") = "USD"
    default_to_currency: constr(regex="^[A-Z]{3}$") = "EUR"
    watched_currencies: Optional[List[constr(regex="^[A-Z]{3}$")]] = None

class TimeZonePreferenceBase(BaseModel):
    default_timezone: str = "UTC"
    watched_timezones: Optional[List[str]] = None
    time_format: TimeFormat = TimeFormat.H24
    date_format: DateFormat = DateFormat.ISO

class GeneratedContentBase(BaseModel):
    content_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    is_favorite: bool = False

class FileConversionBase(BaseModel):
    original_file: str
    source_format: str
    target_format: str
    metadata: Optional[Dict[str, Any]] = None

# Create schemas
class CalculationCreate(CalculationBase):
    pass

class UnitConversionPreferenceCreate(UnitConversionPreferenceBase):
    pass

class CurrencyPreferenceCreate(CurrencyPreferenceBase):
    pass

class TimeZonePreferenceCreate(TimeZonePreferenceBase):
    pass

class GeneratedContentCreate(GeneratedContentBase):
    pass

class FileConversionCreate(FileConversionBase):
    pass

# Update schemas
class UnitConversionPreferenceUpdate(BaseModel):
    default_length_unit: Optional[str] = None
    default_weight_unit: Optional[str] = None
    default_temperature_unit: Optional[str] = None
    default_volume_unit: Optional[str] = None
    default_speed_unit: Optional[str] = None
    default_area_unit: Optional[str] = None

class CurrencyPreferenceUpdate(BaseModel):
    default_from_currency: Optional[constr(regex="^[A-Z]{3}$")] = None
    default_to_currency: Optional[constr(regex="^[A-Z]{3}$")] = None
    watched_currencies: Optional[List[constr(regex="^[A-Z]{3}$")]] = None

class TimeZonePreferenceUpdate(BaseModel):
    default_timezone: Optional[str] = None
    watched_timezones: Optional[List[str]] = None
    time_format: Optional[TimeFormat] = None
    date_format: Optional[DateFormat] = None

class GeneratedContentUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_favorite: Optional[bool] = None

# Response schemas
class CalculationHistory(CalculationBase):
    id: int
    user_id: int
    result: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class UnitConversionPreference(UnitConversionPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CurrencyPreference(CurrencyPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TimeZonePreference(TimeZonePreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GeneratedContent(GeneratedContentBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class FileConversion(FileConversionBase):
    id: int
    user_id: int
    converted_file: str
    status: ConversionStatus
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional request/response schemas
class FinancialCalculationRequest(BaseModel):
    calculation_type: str = Field(..., description="Type of financial calculation")
    principal: float = Field(..., gt=0)
    rate: float = Field(..., ge=0)
    time: float = Field(..., gt=0)
    additional_params: Optional[Dict[str, Any]] = None

class UnitConversionRequest(BaseModel):
    value: float
    from_unit: str
    to_unit: str
    unit_type: str = Field(..., description="length, weight, temperature, etc.")

class CurrencyConversionRequest(BaseModel):
    amount: float = Field(..., gt=0)
    from_currency: constr(regex="^[A-Z]{3}$")
    to_currency: constr(regex="^[A-Z]{3}$")

class TimeZoneConversionRequest(BaseModel):
    datetime: datetime
    from_timezone: str
    to_timezone: str

class PasswordGenerationRequest(BaseModel):
    length: int = Field(..., ge=8, le=128)
    include_uppercase: bool = True
    include_lowercase: bool = True
    include_numbers: bool = True
    include_special: bool = True
    exclude_similar: bool = False
    exclude_ambiguous: bool = False

class QRCodeGenerationRequest(BaseModel):
    content: str
    size: int = Field(default=200, ge=100, le=1000)
    error_correction: str = Field(default="M", regex="^[LMQH]$")
    format: str = Field(default="PNG", regex="^(PNG|SVG)$")

class TextToolRequest(BaseModel):
    text: str
    operation: str = Field(..., description="encode, decode, format, etc.")
    format: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None

# Response schemas for calculations and conversions
class CalculationResponse(BaseModel):
    result: Union[float, Dict[str, Any]]
    formatted_result: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversionResponse(BaseModel):
    result: float
    formatted_result: str
    rate: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class GenerationResponse(BaseModel):
    content: str
    format: str
    metadata: Optional[Dict[str, Any]] = None 