from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from fastapi import HTTPException

from app.models.shopping import (
    Deal, PriceHistory, PriceAlert, ShoppingList, ShoppingItem,
    Purchase, ShoppingPreference, DealStatus, PriceAlertStatus,
    ShoppingListStatus
)
from app.schemas.shopping import (
    DealCreate, DealUpdate, PriceAlertCreate, PriceAlertUpdate,
    ShoppingListCreate, ShoppingListUpdate, ShoppingItemCreate,
    ShoppingItemUpdate, PurchaseCreate, ShoppingPreferenceCreate,
    ShoppingPreferenceUpdate, DealSearchParams
)

class ShoppingService:
    def __init__(self, db: Session):
        self.db = db

    # Deal methods
    def create_deal(self, deal_in: DealCreate) -> Deal:
        deal = Deal(**deal_in.dict())
        self.db.add(deal)
        self.db.commit()
        self.db.refresh(deal)
        return deal

    def get_deal(self, deal_id: int) -> Optional[Deal]:
        return self.db.query(Deal).filter(Deal.id == deal_id).first()

    def get_deals(
        self,
        skip: int = 0,
        limit: int = 100,
        store: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[DealStatus] = None
    ) -> List[Deal]:
        query = self.db.query(Deal)

        if store:
            query = query.filter(Deal.store == store)
        if category:
            query = query.filter(Deal.category == category)
        if status:
            query = query.filter(Deal.status == status)

        return (
            query.order_by(desc(Deal.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_deal(
        self,
        deal_id: int,
        deal_in: DealUpdate
    ) -> Optional[Deal]:
        deal = self.get_deal(deal_id)
        if not deal:
            return None

        for field, value in deal_in.dict(exclude_unset=True).items():
            setattr(deal, field, value)

        self.db.commit()
        self.db.refresh(deal)
        return deal

    def delete_deal(self, deal_id: int) -> bool:
        deal = self.get_deal(deal_id)
        if not deal:
            return False

        self.db.delete(deal)
        self.db.commit()
        return True

    def search_deals(
        self,
        params: DealSearchParams,
        user_id: Optional[int] = None
    ) -> List[Deal]:
        query = self.db.query(Deal)

        if params.query:
            query = query.filter(
                Deal.title.ilike(f"%{params.query}%") |
                Deal.description.ilike(f"%{params.query}%")
            )

        if params.store:
            query = query.filter(Deal.store == params.store)

        if params.category:
            query = query.filter(Deal.category == params.category)

        if params.min_discount:
            query = query.filter(Deal.discount_percentage >= params.min_discount)

        if params.max_price:
            query = query.filter(Deal.deal_price <= params.max_price)

        if params.status:
            query = query.filter(Deal.status == params.status)

        if params.sort_by == "discount":
            query = query.order_by(desc(Deal.discount_percentage))
        elif params.sort_by == "price":
            query = query.order_by(Deal.deal_price)
        else:  # date
            query = query.order_by(desc(Deal.created_at))

        return query.offset((params.page - 1) * params.per_page).limit(params.per_page).all()

    # Price alert methods
    def create_price_alert(
        self,
        user_id: int,
        alert_in: PriceAlertCreate
    ) -> PriceAlert:
        alert = PriceAlert(**alert_in.dict(), user_id=user_id)
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get_user_price_alerts(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[PriceAlertStatus] = None
    ) -> List[PriceAlert]:
        query = self.db.query(PriceAlert).filter(PriceAlert.user_id == user_id)

        if status:
            query = query.filter(PriceAlert.status == status)

        return (
            query.order_by(desc(PriceAlert.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_price_alert(
        self,
        user_id: int,
        alert_id: int,
        alert_in: PriceAlertUpdate
    ) -> Optional[PriceAlert]:
        alert = (
            self.db.query(PriceAlert)
            .filter(
                PriceAlert.id == alert_id,
                PriceAlert.user_id == user_id
            )
            .first()
        )
        if not alert:
            return None

        for field, value in alert_in.dict(exclude_unset=True).items():
            setattr(alert, field, value)

        self.db.commit()
        self.db.refresh(alert)
        return alert

    def delete_price_alert(
        self,
        user_id: int,
        alert_id: int
    ) -> bool:
        alert = (
            self.db.query(PriceAlert)
            .filter(
                PriceAlert.id == alert_id,
                PriceAlert.user_id == user_id
            )
            .first()
        )
        if not alert:
            return False

        self.db.delete(alert)
        self.db.commit()
        return True

    # Shopping list methods
    def create_shopping_list(
        self,
        user_id: int,
        list_in: ShoppingListCreate
    ) -> ShoppingList:
        shopping_list = ShoppingList(**list_in.dict(), user_id=user_id)
        self.db.add(shopping_list)
        self.db.commit()
        self.db.refresh(shopping_list)
        return shopping_list

    def get_user_shopping_lists(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ShoppingListStatus] = None
    ) -> List[ShoppingList]:
        query = self.db.query(ShoppingList).filter(ShoppingList.user_id == user_id)

        if status:
            query = query.filter(ShoppingList.status == status)

        return (
            query.order_by(desc(ShoppingList.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_shopping_list(
        self,
        user_id: int,
        list_id: int,
        list_in: ShoppingListUpdate
    ) -> Optional[ShoppingList]:
        shopping_list = (
            self.db.query(ShoppingList)
            .filter(
                ShoppingList.id == list_id,
                ShoppingList.user_id == user_id
            )
            .first()
        )
        if not shopping_list:
            return None

        for field, value in list_in.dict(exclude_unset=True).items():
            setattr(shopping_list, field, value)

        if list_in.status == ShoppingListStatus.COMPLETED:
            shopping_list.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(shopping_list)
        return shopping_list

    def delete_shopping_list(
        self,
        user_id: int,
        list_id: int
    ) -> bool:
        shopping_list = (
            self.db.query(ShoppingList)
            .filter(
                ShoppingList.id == list_id,
                ShoppingList.user_id == user_id
            )
            .first()
        )
        if not shopping_list:
            return False

        self.db.delete(shopping_list)
        self.db.commit()
        return True

    # Shopping item methods
    def create_shopping_item(
        self,
        user_id: int,
        item_in: ShoppingItemCreate
    ) -> ShoppingItem:
        # Verify the shopping list belongs to the user
        shopping_list = (
            self.db.query(ShoppingList)
            .filter(
                ShoppingList.id == item_in.shopping_list_id,
                ShoppingList.user_id == user_id
            )
            .first()
        )
        if not shopping_list:
            raise HTTPException(status_code=404, detail="Shopping list not found")

        item = ShoppingItem(**item_in.dict())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_shopping_item(
        self,
        user_id: int,
        item_id: int,
        item_in: ShoppingItemUpdate
    ) -> Optional[ShoppingItem]:
        # Get the item and verify it belongs to a list owned by the user
        item = (
            self.db.query(ShoppingItem)
            .join(ShoppingList)
            .filter(
                ShoppingItem.id == item_id,
                ShoppingList.user_id == user_id
            )
            .first()
        )
        if not item:
            return None

        for field, value in item_in.dict(exclude_unset=True).items():
            setattr(item, field, value)

        if item_in.is_purchased:
            item.purchased_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_shopping_item(
        self,
        user_id: int,
        item_id: int
    ) -> bool:
        # Get the item and verify it belongs to a list owned by the user
        item = (
            self.db.query(ShoppingItem)
            .join(ShoppingList)
            .filter(
                ShoppingItem.id == item_id,
                ShoppingList.user_id == user_id
            )
            .first()
        )
        if not item:
            return False

        self.db.delete(item)
        self.db.commit()
        return True

    # Purchase methods
    def create_purchase(
        self,
        user_id: int,
        purchase_in: PurchaseCreate
    ) -> Purchase:
        purchase = Purchase(**purchase_in.dict(), user_id=user_id)
        self.db.add(purchase)
        self.db.commit()
        self.db.refresh(purchase)
        return purchase

    def get_user_purchases(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Purchase]:
        query = self.db.query(Purchase).filter(Purchase.user_id == user_id)

        if start_date:
            query = query.filter(Purchase.purchase_date >= start_date)
        if end_date:
            query = query.filter(Purchase.purchase_date <= end_date)

        return (
            query.order_by(desc(Purchase.purchase_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    # Shopping preference methods
    def get_or_create_preference(
        self,
        user_id: int
    ) -> ShoppingPreference:
        preference = (
            self.db.query(ShoppingPreference)
            .filter(ShoppingPreference.user_id == user_id)
            .first()
        )
        if not preference:
            preference = ShoppingPreference(user_id=user_id)
            self.db.add(preference)
            self.db.commit()
            self.db.refresh(preference)
        return preference

    def update_preference(
        self,
        user_id: int,
        preference_in: ShoppingPreferenceUpdate
    ) -> ShoppingPreference:
        preference = self.get_or_create_preference(user_id)

        for field, value in preference_in.dict(exclude_unset=True).items():
            setattr(preference, field, value)

        self.db.commit()
        self.db.refresh(preference)
        return preference

    # Statistics methods
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        # Calculate total spent and saved
        purchases = (
            self.db.query(
                func.sum(Purchase.total_amount).label("total_spent"),
                func.count(Purchase.id).label("total_purchases")
            )
            .filter(Purchase.user_id == user_id)
            .first()
        )
        total_spent = purchases[0] or 0
        total_purchases = purchases[1] or 0

        # Calculate total saved from deals
        saved_from_deals = (
            self.db.query(func.sum(Deal.original_price - Deal.deal_price))
            .join(Purchase, Purchase.deal_id == Deal.id)
            .filter(Purchase.user_id == user_id)
            .scalar() or 0
        )

        # Get purchases by store
        purchases_by_store = (
            self.db.query(
                Purchase.store,
                func.sum(Purchase.total_amount)
            )
            .filter(Purchase.user_id == user_id)
            .group_by(Purchase.store)
            .all()
        )

        # Get purchases by category
        purchases_by_category = (
            self.db.query(
                Deal.category,
                func.sum(Purchase.total_amount)
            )
            .join(Purchase, Purchase.deal_id == Deal.id)
            .filter(Purchase.user_id == user_id)
            .group_by(Deal.category)
            .all()
        )

        # Calculate average discount
        avg_discount = (
            self.db.query(func.avg(Deal.discount_percentage))
            .join(Purchase, Purchase.deal_id == Deal.id)
            .filter(Purchase.user_id == user_id)
            .scalar() or 0
        )

        # Count active price alerts
        active_alerts = (
            self.db.query(func.count(PriceAlert.id))
            .filter(
                PriceAlert.user_id == user_id,
                PriceAlert.status == PriceAlertStatus.ACTIVE
            )
            .scalar() or 0
        )

        # Get shopping lists statistics
        shopping_lists_stats = (
            self.db.query(
                ShoppingList.status,
                func.count(ShoppingList.id)
            )
            .filter(ShoppingList.user_id == user_id)
            .group_by(ShoppingList.status)
            .all()
        )

        return {
            "total_spent": total_spent,
            "total_saved": saved_from_deals,
            "purchases_by_store": dict(purchases_by_store),
            "purchases_by_category": dict(purchases_by_category),
            "average_discount": avg_discount,
            "total_purchases": total_purchases,
            "active_price_alerts": active_alerts,
            "shopping_lists_stats": dict(shopping_lists_stats)
        } 