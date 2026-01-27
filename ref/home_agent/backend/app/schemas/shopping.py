from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl, EmailStr, Field, constr, confloat

from app.models.shopping import DealStatus, PriceAlertStatus, ShoppingListStatus

# Base schemas
class DealBase(BaseModel):
    title: str
    description: Optional[str] = None
    original_price: confloat(gt=0)
    deal_price: confloat(gt=0)
    discount_percentage: confloat(ge=0, le=100)
    url: HttpUrl
    image_url: Optional[HttpUrl] = None
    store: str
    category: str
    start_date: datetime
    end_date: Optional[datetime] = None
    terms_conditions: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PriceHistoryBase(BaseModel):
    deal_id: int
    price: confloat(gt=0)

class PriceAlertBase(BaseModel):
    deal_id: int
    target_price: confloat(gt=0)
    notification_email: Optional[EmailStr] = None
    notification_mobile: Optional[str] = None

class ShoppingListBase(BaseModel):
    name: str
    description: Optional[str] = None
    total_budget: Optional[confloat(gt=0)] = None

class ShoppingItemBase(BaseModel):
    name: str
    quantity: int = Field(ge=1)
    unit: Optional[str] = None
    estimated_price: Optional[confloat(gt=0)] = None
    notes: Optional[str] = None

class PurchaseBase(BaseModel):
    deal_id: Optional[int] = None
    store: str
    total_amount: confloat(gt=0)
    purchase_date: datetime
    notes: Optional[str] = None

class ShoppingPreferenceBase(BaseModel):
    preferred_stores: Optional[List[str]] = None
    excluded_stores: Optional[List[str]] = None
    preferred_categories: Optional[List[str]] = None
    min_discount_percentage: Optional[confloat(ge=0, le=100)] = None
    max_price_threshold: Optional[confloat(gt=0)] = None
    notification_email: Optional[EmailStr] = None
    notification_mobile: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None

# Create schemas
class DealCreate(DealBase):
    pass

class PriceHistoryCreate(PriceHistoryBase):
    pass

class PriceAlertCreate(PriceAlertBase):
    pass

class ShoppingListCreate(ShoppingListBase):
    pass

class ShoppingItemCreate(ShoppingItemBase):
    shopping_list_id: int

class PurchaseCreate(PurchaseBase):
    pass

class ShoppingPreferenceCreate(ShoppingPreferenceBase):
    pass

# Update schemas
class DealUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    original_price: Optional[confloat(gt=0)] = None
    deal_price: Optional[confloat(gt=0)] = None
    discount_percentage: Optional[confloat(ge=0, le=100)] = None
    url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = None
    store: Optional[str] = None
    category: Optional[str] = None
    status: Optional[DealStatus] = None
    end_date: Optional[datetime] = None
    terms_conditions: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PriceAlertUpdate(BaseModel):
    target_price: Optional[confloat(gt=0)] = None
    status: Optional[PriceAlertStatus] = None
    notification_email: Optional[EmailStr] = None
    notification_mobile: Optional[str] = None

class ShoppingListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ShoppingListStatus] = None
    total_budget: Optional[confloat(gt=0)] = None

class ShoppingItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=1)
    unit: Optional[str] = None
    estimated_price: Optional[confloat(gt=0)] = None
    actual_price: Optional[confloat(gt=0)] = None
    notes: Optional[str] = None
    is_purchased: Optional[bool] = None

class ShoppingPreferenceUpdate(ShoppingPreferenceBase):
    pass

# Response schemas
class PriceHistory(PriceHistoryBase):
    id: int
    recorded_at: datetime

    class Config:
        from_attributes = True

class PriceAlert(PriceAlertBase):
    id: int
    user_id: int
    status: PriceAlertStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ShoppingItem(ShoppingItemBase):
    id: int
    shopping_list_id: int
    actual_price: Optional[confloat(gt=0)] = None
    is_purchased: bool
    purchased_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ShoppingList(ShoppingListBase):
    id: int
    user_id: int
    status: ShoppingListStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items: List[ShoppingItem]

    class Config:
        from_attributes = True

class Deal(DealBase):
    id: int
    status: DealStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    price_history: List[PriceHistory]

    class Config:
        from_attributes = True

class Purchase(PurchaseBase):
    id: int
    user_id: int
    receipt_url: Optional[HttpUrl] = None
    created_at: datetime
    deal: Optional[Deal] = None

    class Config:
        from_attributes = True

class ShoppingPreference(ShoppingPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional schemas for specific operations
class DealSearchParams(BaseModel):
    query: Optional[str] = None
    store: Optional[str] = None
    category: Optional[str] = None
    min_discount: Optional[confloat(ge=0, le=100)] = None
    max_price: Optional[confloat(gt=0)] = None
    status: Optional[DealStatus] = None
    sort_by: Optional[str] = "discount"  # discount, price, date
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

class ShoppingStats(BaseModel):
    total_spent: float
    total_saved: float
    purchases_by_store: Dict[str, float]
    purchases_by_category: Dict[str, float]
    average_discount: float
    total_purchases: int
    active_price_alerts: int
    shopping_lists_stats: Dict[str, int]  # active, completed, archived counts 