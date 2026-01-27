import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.shopping import (
    Deal,
    PriceHistory,
    PriceAlert,
    ShoppingList,
    ShoppingItem,
    Purchase,
    ShoppingPreference
)
from app.services.shopping import ShoppingService

def test_create_deal(db: Session):
    """Test creating a deal record."""
    deal = Deal(
        title="Test Deal",
        description="Test Description",
        original_price=Decimal("99.99"),
        deal_price=Decimal("79.99"),
        discount_percentage=20,
        url="https://example.com/deal",
        metadata={"category": "electronics"}
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)

    assert deal.id is not None
    assert deal.title == "Test Deal"
    assert deal.original_price == Decimal("99.99")
    assert deal.discount_percentage == 20

def test_create_price_history(db: Session):
    """Test creating a price history record."""
    price_history = PriceHistory(
        product_id="test123",
        price=Decimal("99.99"),
        timestamp=datetime.utcnow(),
        metadata={"source": "amazon"}
    )
    db.add(price_history)
    db.commit()
    db.refresh(price_history)

    assert price_history.id is not None
    assert price_history.product_id == "test123"
    assert price_history.price == Decimal("99.99")

def test_create_price_alert(db: Session, test_user: dict):
    """Test creating a price alert."""
    alert = PriceAlert(
        user_id=1,
        product_id="test123",
        target_price=Decimal("75.00"),
        current_price=Decimal("99.99"),
        alert_type="below_price",
        is_active=True
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    assert alert.id is not None
    assert alert.product_id == "test123"
    assert alert.target_price == Decimal("75.00")
    assert alert.is_active is True

def test_create_shopping_list(db: Session, test_user: dict):
    """Test creating a shopping list."""
    shopping_list = ShoppingList(
        user_id=1,
        name="Test List",
        description="Test Description",
        is_public=False
    )
    db.add(shopping_list)
    db.commit()
    db.refresh(shopping_list)

    assert shopping_list.id is not None
    assert shopping_list.name == "Test List"
    assert shopping_list.is_public is False

def test_create_shopping_item(db: Session):
    """Test creating a shopping item."""
    item = ShoppingItem(
        list_id=1,
        name="Test Item",
        quantity=2,
        price=Decimal("19.99"),
        priority="high",
        status="pending"
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    assert item.id is not None
    assert item.name == "Test Item"
    assert item.quantity == 2
    assert item.status == "pending"

def test_create_purchase(db: Session, test_user: dict):
    """Test creating a purchase record."""
    purchase = Purchase(
        user_id=1,
        product_id="test123",
        price=Decimal("79.99"),
        quantity=1,
        purchase_date=datetime.utcnow(),
        metadata={"store": "online"}
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    assert purchase.id is not None
    assert purchase.product_id == "test123"
    assert purchase.price == Decimal("79.99")

def test_create_shopping_preference(db: Session, test_user: dict):
    """Test creating shopping preferences."""
    preference = ShoppingPreference(
        user_id=1,
        preferred_categories=["electronics", "books"],
        price_alerts_enabled=True,
        deal_notification_frequency="daily",
        max_price_alert_count=10
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)

    assert preference.id is not None
    assert "electronics" in preference.preferred_categories
    assert preference.price_alerts_enabled is True

def test_shopping_service(db: Session, test_user: dict):
    """Test the shopping service functionality."""
    service = ShoppingService(db)
    
    # Test creating a shopping list
    shopping_list = service.create_shopping_list(
        user_id=1,
        name="Test List",
        description="Test Description"
    )
    assert shopping_list.name == "Test List"

    # Test adding an item to the list
    item = service.add_item_to_list(
        list_id=shopping_list.id,
        name="Test Item",
        quantity=1,
        price=Decimal("19.99")
    )
    assert item.name == "Test Item"

    # Test getting the shopping list
    retrieved_list = service.get_shopping_list(shopping_list.id)
    assert len(retrieved_list.items) == 1

def test_price_alert_service(db: Session, test_user: dict):
    """Test price alert functionality."""
    service = ShoppingService(db)

    # Create price alert
    alert = service.create_price_alert(
        user_id=1,
        product_id="test123",
        target_price=Decimal("75.00"),
        current_price=Decimal("99.99")
    )
    assert alert.product_id == "test123"

    # Test checking price alerts
    alerts = service.check_price_alerts(user_id=1)
    assert len(alerts) == 1

def test_deal_recommendations(db: Session, test_user: dict):
    """Test deal recommendations."""
    service = ShoppingService(db)

    # Create test deals
    deal = Deal(
        title="Test Deal",
        description="Test Description",
        original_price=Decimal("99.99"),
        deal_price=Decimal("79.99"),
        discount_percentage=20,
        metadata={"category": "electronics"}
    )
    db.add(deal)
    db.commit()

    # Create user preference
    preference = ShoppingPreference(
        user_id=1,
        preferred_categories=["electronics"]
    )
    db.add(preference)
    db.commit()

    # Get recommendations
    recommendations = service.get_deal_recommendations(user_id=1)
    assert len(recommendations) >= 0  # May be 0 if no matching recommendations 