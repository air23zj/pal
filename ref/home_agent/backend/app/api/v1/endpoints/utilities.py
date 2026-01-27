from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.utilities import UtilitiesService
from app.schemas.utilities import (
    CalculationCreate, CalculationHistory, UnitConversionPreference,
    CurrencyPreference, TimeZonePreference, GeneratedContent, FileConversion,
    UnitConversionPreferenceUpdate, CurrencyPreferenceUpdate, TimeZonePreferenceUpdate,
    GeneratedContentUpdate, FinancialCalculationRequest, UnitConversionRequest,
    CurrencyConversionRequest, TimeZoneConversionRequest, PasswordGenerationRequest,
    QRCodeGenerationRequest, TextToolRequest, CalculationResponse, ConversionResponse,
    GenerationResponse, ConversionStatus, FileConversionCreate
)

router = APIRouter()

@router.post("/calculations", response_model=CalculationHistory)
def create_calculation(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    calculation_in: CalculationCreate
) -> CalculationHistory:
    """
    Create a new calculation.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.create_calculation(current_user.id, calculation_in)

@router.get("/calculations", response_model=List[CalculationHistory])
def get_calculation_history(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    calculation_type: Optional[str] = None
) -> List[CalculationHistory]:
    """
    Retrieve calculation history.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.get_calculation_history(
        current_user.id,
        skip=skip,
        limit=limit,
        calculation_type=calculation_type
    )

@router.get("/preferences/unit-conversion", response_model=UnitConversionPreference)
def get_unit_conversion_preference(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> UnitConversionPreference:
    """
    Get unit conversion preferences.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.get_or_create_unit_conversion_preference(current_user.id)

@router.put("/preferences/unit-conversion", response_model=UnitConversionPreference)
def update_unit_conversion_preference(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    preference_in: UnitConversionPreferenceUpdate
) -> UnitConversionPreference:
    """
    Update unit conversion preferences.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.update_unit_conversion_preference(current_user.id, preference_in)

@router.get("/preferences/currency", response_model=CurrencyPreference)
def get_currency_preference(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> CurrencyPreference:
    """
    Get currency preferences.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.get_or_create_currency_preference(current_user.id)

@router.put("/preferences/currency", response_model=CurrencyPreference)
def update_currency_preference(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    preference_in: CurrencyPreferenceUpdate
) -> CurrencyPreference:
    """
    Update currency preferences.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.update_currency_preference(current_user.id, preference_in)

@router.get("/preferences/timezone", response_model=TimeZonePreference)
def get_timezone_preference(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> TimeZonePreference:
    """
    Get timezone preferences.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.get_or_create_timezone_preference(current_user.id)

@router.put("/preferences/timezone", response_model=TimeZonePreference)
def update_timezone_preference(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    preference_in: TimeZonePreferenceUpdate
) -> TimeZonePreference:
    """
    Update timezone preferences.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.update_timezone_preference(current_user.id, preference_in)

@router.post("/generate/password", response_model=GeneratedContent)
def generate_password(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    request: PasswordGenerationRequest
) -> GeneratedContent:
    """
    Generate a password.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.generate_password(current_user.id, request)

@router.post("/generate/qr-code", response_model=GeneratedContent)
def generate_qr_code(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    request: QRCodeGenerationRequest
) -> GeneratedContent:
    """
    Generate a QR code.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.generate_qr_code(current_user.id, request)

@router.post("/text/process", response_model=GeneratedContent)
def process_text(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    request: TextToolRequest
) -> GeneratedContent:
    """
    Process text (encode, decode, format).
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.process_text(current_user.id, request)

@router.get("/generated-content", response_model=List[GeneratedContent])
def get_generated_content(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    content_type: Optional[str] = None
) -> List[GeneratedContent]:
    """
    Retrieve generated content.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.get_generated_content(
        current_user.id,
        skip=skip,
        limit=limit,
        content_type=content_type
    )

@router.put("/generated-content/{content_id}", response_model=GeneratedContent)
def update_generated_content(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    content_id: int,
    content_in: GeneratedContentUpdate
) -> GeneratedContent:
    """
    Update generated content.
    """
    utilities_service = UtilitiesService(db)
    content = utilities_service.update_generated_content(content_id, content_in)
    if not content:
        raise HTTPException(status_code=404, detail="Generated content not found")
    return content

@router.delete("/generated-content/{content_id}")
def delete_generated_content(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    content_id: int
) -> bool:
    """
    Delete generated content.
    """
    utilities_service = UtilitiesService(db)
    if not utilities_service.delete_generated_content(content_id):
        raise HTTPException(status_code=404, detail="Generated content not found")
    return True

@router.post("/file-conversions", response_model=FileConversion)
def create_file_conversion(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    conversion_in: FileConversionCreate
) -> FileConversion:
    """
    Create a new file conversion.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.create_file_conversion(current_user.id, conversion_in)

@router.get("/file-conversions/{conversion_id}", response_model=FileConversion)
def get_file_conversion(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    conversion_id: int
) -> FileConversion:
    """
    Get a specific file conversion.
    """
    utilities_service = UtilitiesService(db)
    conversion = utilities_service.get_file_conversion(conversion_id)
    if not conversion:
        raise HTTPException(status_code=404, detail="File conversion not found")
    return conversion

@router.get("/file-conversions", response_model=List[FileConversion])
def get_user_file_conversions(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[ConversionStatus] = None
) -> List[FileConversion]:
    """
    Get all file conversions for a user.
    """
    utilities_service = UtilitiesService(db)
    return utilities_service.get_user_file_conversions(
        current_user.id,
        skip=skip,
        limit=limit,
        status=status
    ) 