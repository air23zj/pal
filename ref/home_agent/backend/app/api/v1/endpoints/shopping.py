from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.shopping import ShoppingService
from app.schemas.shopping import (
    Deal, PriceHistory, PriceAlert, ShoppingList, ShoppingItem,
    Purchase, ShoppingPreference, ShoppingStats, DealSearchParams,
    DealCreate, DealUpdate, PriceAlertCreate, PriceAlertUpdate,
    ShoppingListCreate, ShoppingListUpdate, ShoppingItemCreate,
    ShoppingItemUpdate, PurchaseCreate, ShoppingPreferenceUpdate
)

router = APIRouter()

# Deal endpoints
@router.post("/deals", response_model=Deal)
def create_deal(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    deal_in: DealCreate
) -> Deal:
    """
    Create a new deal.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    shopping_service = ShoppingService(db)
    return shopping_service.create_deal(deal_in)

@router.get("/deals", response_model=List[Deal])
def get_deals(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    store: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None
) -> List[Deal]:
    """
    Retrieve deals.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.get_deals(
        skip=skip,
        limit=limit,
        store=store,
        category=category,
        status=status
    )

@router.get("/deals/{deal_id}", response_model=Deal)
def get_deal(
    *,
    db: Session = Depends(deps.get_db),
    deal_id: int
) -> Deal:
    """
    Get a specific deal.
    """
    shopping_service = ShoppingService(db)
    deal = shopping_service.get_deal(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

@router.put("/deals/{deal_id}", response_model=Deal)
def update_deal(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    deal_id: int,
    deal_in: DealUpdate
) -> Deal:
    """
    Update a deal.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    shopping_service = ShoppingService(db)
    deal = shopping_service.update_deal(deal_id, deal_in)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

@router.delete("/deals/{deal_id}")
def delete_deal(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    deal_id: int
) -> bool:
    """
    Delete a deal.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    shopping_service = ShoppingService(db)
    if not shopping_service.delete_deal(deal_id):
        raise HTTPException(status_code=404, detail="Deal not found")
    return True

@router.post("/deals/search", response_model=List[Deal])
def search_deals(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    params: DealSearchParams
) -> List[Deal]:
    """
    Search deals.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.search_deals(params, current_user.id)

# Price alert endpoints
@router.post("/price-alerts", response_model=PriceAlert)
def create_price_alert(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    alert_in: PriceAlertCreate
) -> PriceAlert:
    """
    Create a new price alert.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.create_price_alert(current_user.id, alert_in)

@router.get("/price-alerts", response_model=List[PriceAlert])
def get_price_alerts(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None
) -> List[PriceAlert]:
    """
    Retrieve user's price alerts.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.get_user_price_alerts(
        current_user.id,
        skip=skip,
        limit=limit,
        status=status
    )

@router.put("/price-alerts/{alert_id}", response_model=PriceAlert)
def update_price_alert(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    alert_id: int,
    alert_in: PriceAlertUpdate
) -> PriceAlert:
    """
    Update a price alert.
    """
    shopping_service = ShoppingService(db)
    alert = shopping_service.update_price_alert(current_user.id, alert_id, alert_in)
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    return alert

@router.delete("/price-alerts/{alert_id}")
def delete_price_alert(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    alert_id: int
) -> bool:
    """
    Delete a price alert.
    """
    shopping_service = ShoppingService(db)
    if not shopping_service.delete_price_alert(current_user.id, alert_id):
        raise HTTPException(status_code=404, detail="Price alert not found")
    return True

# Shopping list endpoints
@router.post("/shopping-lists", response_model=ShoppingList)
def create_shopping_list(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    list_in: ShoppingListCreate
) -> ShoppingList:
    """
    Create a new shopping list.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.create_shopping_list(current_user.id, list_in)

@router.get("/shopping-lists", response_model=List[ShoppingList])
def get_shopping_lists(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None
) -> List[ShoppingList]:
    """
    Retrieve user's shopping lists.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.get_user_shopping_lists(
        current_user.id,
        skip=skip,
        limit=limit,
        status=status
    )

@router.put("/shopping-lists/{list_id}", response_model=ShoppingList)
def update_shopping_list(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    list_id: int,
    list_in: ShoppingListUpdate
) -> ShoppingList:
    """
    Update a shopping list.
    """
    shopping_service = ShoppingService(db)
    shopping_list = shopping_service.update_shopping_list(current_user.id, list_id, list_in)
    if not shopping_list:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return shopping_list

@router.delete("/shopping-lists/{list_id}")
def delete_shopping_list(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    list_id: int
) -> bool:
    """
    Delete a shopping list.
    """
    shopping_service = ShoppingService(db)
    if not shopping_service.delete_shopping_list(current_user.id, list_id):
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return True

# Shopping item endpoints
@router.post("/shopping-items", response_model=ShoppingItem)
def create_shopping_item(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    item_in: ShoppingItemCreate
) -> ShoppingItem:
    """
    Create a new shopping item.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.create_shopping_item(current_user.id, item_in)

@router.put("/shopping-items/{item_id}", response_model=ShoppingItem)
def update_shopping_item(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    item_id: int,
    item_in: ShoppingItemUpdate
) -> ShoppingItem:
    """
    Update a shopping item.
    """
    shopping_service = ShoppingService(db)
    item = shopping_service.update_shopping_item(current_user.id, item_id, item_in)
    if not item:
        raise HTTPException(status_code=404, detail="Shopping item not found")
    return item

@router.delete("/shopping-items/{item_id}")
def delete_shopping_item(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    item_id: int
) -> bool:
    """
    Delete a shopping item.
    """
    shopping_service = ShoppingService(db)
    if not shopping_service.delete_shopping_item(current_user.id, item_id):
        raise HTTPException(status_code=404, detail="Shopping item not found")
    return True

# Purchase endpoints
@router.post("/purchases", response_model=Purchase)
def create_purchase(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    purchase_in: PurchaseCreate
) -> Purchase:
    """
    Create a new purchase.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.create_purchase(current_user.id, purchase_in)

@router.get("/purchases", response_model=List[Purchase])
def get_purchases(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Purchase]:
    """
    Retrieve user's purchases.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.get_user_purchases(
        current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )

# Shopping preference endpoints
@router.get("/preferences", response_model=ShoppingPreference)
def get_preferences(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> ShoppingPreference:
    """
    Get user's shopping preferences.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.get_or_create_preference(current_user.id)

@router.put("/preferences", response_model=ShoppingPreference)
def update_preferences(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    preference_in: ShoppingPreferenceUpdate
) -> ShoppingPreference:
    """
    Update user's shopping preferences.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.update_preference(current_user.id, preference_in)

# Statistics endpoints
@router.get("/stats", response_model=ShoppingStats)
def get_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> ShoppingStats:
    """
    Get user's shopping statistics.
    """
    shopping_service = ShoppingService(db)
    return shopping_service.get_user_stats(current_user.id) 