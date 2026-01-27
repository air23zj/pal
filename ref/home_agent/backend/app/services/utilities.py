from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import pytz
import qrcode
import secrets
import string
import base64
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.utilities import (
    CalculationHistory, UnitConversionPreference, CurrencyPreference,
    TimeZonePreference, GeneratedContent, FileConversion,
    CalculationType
)
from app.schemas.utilities import (
    CalculationCreate, UnitConversionPreferenceCreate, CurrencyPreferenceCreate,
    TimeZonePreferenceCreate, GeneratedContentCreate, FileConversionCreate,
    UnitConversionPreferenceUpdate, CurrencyPreferenceUpdate, TimeZonePreferenceUpdate,
    GeneratedContentUpdate, FinancialCalculationRequest, UnitConversionRequest,
    CurrencyConversionRequest, TimeZoneConversionRequest, PasswordGenerationRequest,
    QRCodeGenerationRequest, TextToolRequest, CalculationResponse, ConversionResponse,
    GenerationResponse, ConversionStatus
)
from app.core.config import settings

class UtilitiesService:
    def __init__(self, db: Session):
        self.db = db

    # Calculation methods
    def create_calculation(
        self,
        user_id: int,
        calculation_in: CalculationCreate
    ) -> CalculationHistory:
        result = self._perform_calculation(calculation_in)
        calculation = CalculationHistory(
            user_id=user_id,
            type=calculation_in.type,
            input_data=calculation_in.input_data,
            result=result
        )
        self.db.add(calculation)
        self.db.commit()
        self.db.refresh(calculation)
        return calculation

    def get_calculation_history(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        calculation_type: Optional[CalculationType] = None
    ) -> List[CalculationHistory]:
        query = self.db.query(CalculationHistory).filter(
            CalculationHistory.user_id == user_id
        )
        if calculation_type:
            query = query.filter(CalculationHistory.type == calculation_type)
        return query.order_by(desc(CalculationHistory.created_at)).offset(skip).limit(limit).all()

    def _perform_calculation(self, calculation_in: CalculationCreate) -> Dict[str, Any]:
        if calculation_in.type == CalculationType.FINANCIAL:
            return self._perform_financial_calculation(calculation_in.input_data)
        elif calculation_in.type == CalculationType.SCIENTIFIC:
            return self._perform_scientific_calculation(calculation_in.input_data)
        elif calculation_in.type == CalculationType.UNIT_CONVERSION:
            return self._perform_unit_conversion(calculation_in.input_data)
        elif calculation_in.type == CalculationType.CURRENCY_CONVERSION:
            return self._perform_currency_conversion(calculation_in.input_data)
        elif calculation_in.type == CalculationType.TIME_ZONE_CONVERSION:
            return self._perform_timezone_conversion(calculation_in.input_data)
        else:
            raise ValueError(f"Unsupported calculation type: {calculation_in.type}")

    def _perform_financial_calculation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        calculation_type = input_data.get("calculation_type")
        principal = Decimal(str(input_data.get("principal", 0)))
        rate = Decimal(str(input_data.get("rate", 0))) / 100
        time = Decimal(str(input_data.get("time", 0)))

        if calculation_type == "simple_interest":
            interest = principal * rate * time
            total = principal + interest
            return {
                "interest": float(interest),
                "total": float(total),
                "formatted": f"${total:,.2f}"
            }
        elif calculation_type == "compound_interest":
            total = principal * (1 + rate) ** time
            interest = total - principal
            return {
                "interest": float(interest),
                "total": float(total),
                "formatted": f"${total:,.2f}"
            }
        else:
            raise ValueError(f"Unsupported financial calculation type: {calculation_type}")

    def _perform_scientific_calculation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement scientific calculations
        pass

    def _perform_unit_conversion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement unit conversion logic
        pass

    def _perform_currency_conversion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement currency conversion logic using an external API
        pass

    def _perform_timezone_conversion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement timezone conversion logic
        pass

    # Preference methods
    def get_or_create_unit_conversion_preference(
        self,
        user_id: int
    ) -> UnitConversionPreference:
        preference = (
            self.db.query(UnitConversionPreference)
            .filter(UnitConversionPreference.user_id == user_id)
            .first()
        )
        if not preference:
            preference = UnitConversionPreference(user_id=user_id)
            self.db.add(preference)
            self.db.commit()
            self.db.refresh(preference)
        return preference

    def update_unit_conversion_preference(
        self,
        user_id: int,
        preference_in: UnitConversionPreferenceUpdate
    ) -> UnitConversionPreference:
        preference = self.get_or_create_unit_conversion_preference(user_id)
        
        update_data = preference_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preference, field, value)
        
        self.db.commit()
        self.db.refresh(preference)
        return preference

    def get_or_create_currency_preference(
        self,
        user_id: int
    ) -> CurrencyPreference:
        preference = (
            self.db.query(CurrencyPreference)
            .filter(CurrencyPreference.user_id == user_id)
            .first()
        )
        if not preference:
            preference = CurrencyPreference(user_id=user_id)
            self.db.add(preference)
            self.db.commit()
            self.db.refresh(preference)
        return preference

    def update_currency_preference(
        self,
        user_id: int,
        preference_in: CurrencyPreferenceUpdate
    ) -> CurrencyPreference:
        preference = self.get_or_create_currency_preference(user_id)
        
        update_data = preference_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preference, field, value)
        
        self.db.commit()
        self.db.refresh(preference)
        return preference

    def get_or_create_timezone_preference(
        self,
        user_id: int
    ) -> TimeZonePreference:
        preference = (
            self.db.query(TimeZonePreference)
            .filter(TimeZonePreference.user_id == user_id)
            .first()
        )
        if not preference:
            preference = TimeZonePreference(user_id=user_id)
            self.db.add(preference)
            self.db.commit()
            self.db.refresh(preference)
        return preference

    def update_timezone_preference(
        self,
        user_id: int,
        preference_in: TimeZonePreferenceUpdate
    ) -> TimeZonePreference:
        preference = self.get_or_create_timezone_preference(user_id)
        
        update_data = preference_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preference, field, value)
        
        self.db.commit()
        self.db.refresh(preference)
        return preference

    # Content generation methods
    def generate_password(
        self,
        user_id: int,
        request: PasswordGenerationRequest
    ) -> GeneratedContent:
        characters = ""
        if request.include_uppercase:
            characters += string.ascii_uppercase
        if request.include_lowercase:
            characters += string.ascii_lowercase
        if request.include_numbers:
            characters += string.digits
        if request.include_special:
            characters += string.punctuation

        if request.exclude_similar:
            characters = characters.translate(str.maketrans("", "", "il1Lo0O"))
        if request.exclude_ambiguous:
            characters = characters.translate(str.maketrans("", "", "{}[]()/'\"\\`~,;:.<>"))

        if not characters:
            raise ValueError("No character set selected for password generation")

        password = "".join(secrets.choice(characters) for _ in range(request.length))
        
        content = GeneratedContent(
            user_id=user_id,
            content_type="password",
            content=password,
            metadata={
                "length": request.length,
                "settings": request.dict(exclude={"length"})
            }
        )
        self.db.add(content)
        self.db.commit()
        self.db.refresh(content)
        return content

    def generate_qr_code(
        self,
        user_id: int,
        request: QRCodeGenerationRequest
    ) -> GeneratedContent:
        qr = qrcode.QRCode(
            version=1,
            error_correction=getattr(qrcode.constants, f"ERROR_CORRECT_{request.error_correction}"),
            box_size=10,
            border=4,
        )
        qr.add_data(request.content)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the image and get the file path
        file_path = f"qr_codes/{user_id}_{datetime.utcnow().timestamp()}.{request.format.lower()}"
        img.save(file_path)
        
        content = GeneratedContent(
            user_id=user_id,
            content_type="qr_code",
            content=file_path,
            metadata={
                "original_content": request.content,
                "size": request.size,
                "format": request.format,
                "error_correction": request.error_correction
            }
        )
        self.db.add(content)
        self.db.commit()
        self.db.refresh(content)
        return content

    def process_text(
        self,
        user_id: int,
        request: TextToolRequest
    ) -> GeneratedContent:
        result = None
        if request.operation == "encode":
            if request.format == "base64":
                result = base64.b64encode(request.text.encode()).decode()
            # Add more encoding formats as needed
        elif request.operation == "decode":
            if request.format == "base64":
                result = base64.b64decode(request.text.encode()).decode()
            # Add more decoding formats as needed
        elif request.operation == "format":
            # Implement text formatting logic
            pass
        else:
            raise ValueError(f"Unsupported text operation: {request.operation}")

        content = GeneratedContent(
            user_id=user_id,
            content_type="text_tool",
            content=result,
            metadata={
                "operation": request.operation,
                "format": request.format,
                "original_text": request.text
            }
        )
        self.db.add(content)
        self.db.commit()
        self.db.refresh(content)
        return content

    def get_generated_content(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        content_type: Optional[str] = None
    ) -> List[GeneratedContent]:
        query = self.db.query(GeneratedContent).filter(
            GeneratedContent.user_id == user_id
        )
        if content_type:
            query = query.filter(GeneratedContent.content_type == content_type)
        return query.order_by(desc(GeneratedContent.created_at)).offset(skip).limit(limit).all()

    def update_generated_content(
        self,
        content_id: int,
        content_in: GeneratedContentUpdate
    ) -> Optional[GeneratedContent]:
        content = (
            self.db.query(GeneratedContent)
            .filter(GeneratedContent.id == content_id)
            .first()
        )
        if not content:
            return None
        
        update_data = content_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(content, field, value)
        
        self.db.commit()
        self.db.refresh(content)
        return content

    def delete_generated_content(self, content_id: int) -> bool:
        content = (
            self.db.query(GeneratedContent)
            .filter(GeneratedContent.id == content_id)
            .first()
        )
        if not content:
            return False
        self.db.delete(content)
        self.db.commit()
        return True

    # File conversion methods
    def create_file_conversion(
        self,
        user_id: int,
        conversion_in: FileConversionCreate
    ) -> FileConversion:
        conversion = FileConversion(
            user_id=user_id,
            original_file=conversion_in.original_file,
            converted_file="",  # Will be set after conversion
            source_format=conversion_in.source_format,
            target_format=conversion_in.target_format,
            metadata=conversion_in.metadata
        )
        self.db.add(conversion)
        self.db.commit()
        self.db.refresh(conversion)
        
        # Start async conversion process
        self._start_conversion_process(conversion.id)
        
        return conversion

    def get_file_conversion(self, conversion_id: int) -> Optional[FileConversion]:
        return (
            self.db.query(FileConversion)
            .filter(FileConversion.id == conversion_id)
            .first()
        )

    def get_user_file_conversions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ConversionStatus] = None
    ) -> List[FileConversion]:
        query = self.db.query(FileConversion).filter(
            FileConversion.user_id == user_id
        )
        if status:
            query = query.filter(FileConversion.status == status)
        return query.order_by(desc(FileConversion.created_at)).offset(skip).limit(limit).all()

    def _start_conversion_process(self, conversion_id: int) -> None:
        # Implement async file conversion process
        pass 