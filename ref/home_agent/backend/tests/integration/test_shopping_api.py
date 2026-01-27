import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.shopping import Deal, ShoppingList, PriceAlert

def test_create_shopping_list(client: TestClient, test_auth_headers: dict):
    """Test creating a new shopping list."""
    list_data = {
        "name": "Test List",
        "description": "Test Description",
        "is_public": False
    }
    response = client.post(
        "/api/v1/shopping/lists/",
        json=list_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test List"
    assert data["is_public"] is False

def test_get_shopping_lists(client: TestClient, test_auth_headers: dict):
    """Test retrieving user's shopping lists."""
    response = client.get(
        "/api/v1/shopping/lists/",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_add_item_to_list(client: TestClient, db: Session, test_auth_headers: dict):
    """Test adding an item to a shopping list."""
    # Create test shopping list
    shopping_list = ShoppingList(
        user_id=1,
        name="Test List"
    )
    db.add(shopping_list)
    db.commit()
    db.refresh(shopping_list)

    # Add item to list
    item_data = {
        "name": "Test Item",
        "quantity": 2,
        "price": "19.99",
        "priority": "high"
    }
    response = client.post(
        f"/api/v1/shopping/lists/{shopping_list.id}/items",
        json=item_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["quantity"] == 2

def test_update_shopping_list(client: TestClient, db: Session, test_auth_headers: dict):
    """Test updating a shopping list."""
    # Create test list
    shopping_list = ShoppingList(
        user_id=1,
        name="Original Name",
        description="Original Description"
    )
    db.add(shopping_list)
    db.commit()
    db.refresh(shopping_list)

    # Update the list
    update_data = {
        "name": "Updated Name",
        "description": "Updated Description",
        "is_public": True
    }
    response = client.put(
        f"/api/v1/shopping/lists/{shopping_list.id}",
        json=update_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["is_public"] is True

def test_create_price_alert(client: TestClient, test_auth_headers: dict):
    """Test creating a price alert."""
    alert_data = {
        "product_id": "test123",
        "target_price": "75.00",
        "current_price": "99.99",
        "alert_type": "below_price"
    }
    response = client.post(
        "/api/v1/shopping/alerts",
        json=alert_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "test123"
    assert Decimal(data["target_price"]) == Decimal("75.00")

def test_get_price_alerts(client: TestClient, test_auth_headers: dict):
    """Test retrieving price alerts."""
    response = client.get(
        "/api/v1/shopping/alerts",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_price_alert(client: TestClient, db: Session, test_auth_headers: dict):
    """Test updating a price alert."""
    # Create test alert
    alert = PriceAlert(
        user_id=1,
        product_id="test123",
        target_price=Decimal("75.00"),
        current_price=Decimal("99.99"),
        is_active=True
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Update the alert
    update_data = {
        "target_price": "80.00",
        "is_active": False
    }
    response = client.put(
        f"/api/v1/shopping/alerts/{alert.id}",
        json=update_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["target_price"]) == Decimal("80.00")
    assert data["is_active"] is False

def test_get_deals(client: TestClient, db: Session, test_auth_headers: dict):
    """Test retrieving deals."""
    # Create test deal
    deal = Deal(
        title="Test Deal",
        description="Test Description",
        original_price=Decimal("99.99"),
        deal_price=Decimal("79.99"),
        discount_percentage=20
    )
    db.add(deal)
    db.commit()

    response = client.get(
        "/api/v1/shopping/deals",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_purchase_history(client: TestClient, test_auth_headers: dict):
    """Test retrieving purchase history."""
    response = client.get(
        "/api/v1/shopping/purchases",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_purchase(client: TestClient, test_auth_headers: dict):
    """Test creating a purchase record."""
    purchase_data = {
        "product_id": "test123",
        "price": "79.99",
        "quantity": 1,
        "metadata": {"store": "online"}
    }
    response = client.post(
        "/api/v1/shopping/purchases",
        json=purchase_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "test123"
    assert Decimal(data["price"]) == Decimal("79.99")

def test_get_shopping_preferences(client: TestClient, test_auth_headers: dict):
    """Test retrieving shopping preferences."""
    response = client.get(
        "/api/v1/shopping/preferences",
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "preferred_categories" in data
    assert "price_alerts_enabled" in data

def test_update_shopping_preferences(client: TestClient, test_auth_headers: dict):
    """Test updating shopping preferences."""
    preferences_data = {
        "preferred_categories": ["electronics", "books"],
        "price_alerts_enabled": True,
        "deal_notification_frequency": "daily",
        "max_price_alert_count": 10
    }
    response = client.put(
        "/api/v1/shopping/preferences",
        json=preferences_data,
        headers=test_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "electronics" in data["preferred_categories"]
    assert data["price_alerts_enabled"] is True

def test_invalid_shopping_operations(client: TestClient, test_auth_headers: dict):
    """Test invalid shopping operations."""
    # Test creating list with invalid data
    invalid_data = {
        "name": "",  # Empty name should be invalid
        "is_public": True
    }
    response = client.post(
        "/api/v1/shopping/lists/",
        json=invalid_data,
        headers=test_auth_headers
    )
    assert response.status_code == 422

    # Test accessing non-existent list
    response = client.get(
        "/api/v1/shopping/lists/99999",
        headers=test_auth_headers
    )
    assert response.status_code == 404

    # Test creating price alert with invalid data
    invalid_alert = {
        "product_id": "test123",
        "target_price": "-10.00"  # Negative price should be invalid
    }
    response = client.post(
        "/api/v1/shopping/alerts",
        json=invalid_alert,
        headers=test_auth_headers
    )
    assert response.status_code == 422 