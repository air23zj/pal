from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, JSON, Text, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.db.base_class import Base

class DealStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    UPCOMING = "upcoming"
    SOLD_OUT = "sold_out"

class PriceAlertStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"
    EXPIRED = "expired"

class ShoppingListStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_price = Column(Float, nullable=False)
    deal_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, nullable=False)
    url = Column(String(500), nullable=False)
    image_url = Column(String(500), nullable=True)
    store = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    status = Column(Enum(DealStatus), default=DealStatus.ACTIVE)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    terms_conditions = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    price_history = relationship("PriceHistory", back_populates="deal", cascade="all, delete-orphan")
    price_alerts = relationship("PriceAlert", back_populates="deal", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    price = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    deal = relationship("Deal", back_populates="price_history")

class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    target_price = Column(Float, nullable=False)
    status = Column(Enum(PriceAlertStatus), default=PriceAlertStatus.ACTIVE)
    notification_email = Column(String(255), nullable=True)
    notification_mobile = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="price_alerts")
    deal = relationship("Deal", back_populates="price_alerts")

class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ShoppingListStatus), default=ShoppingListStatus.ACTIVE)
    total_budget = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="shopping_lists")
    items = relationship("ShoppingItem", back_populates="shopping_list", cascade="all, delete-orphan")

class ShoppingItem(Base):
    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True, index=True)
    shopping_list_id = Column(Integer, ForeignKey("shopping_lists.id"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    unit = Column(String(50), nullable=True)
    estimated_price = Column(Float, nullable=True)
    actual_price = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    is_purchased = Column(Boolean, default=False)
    purchased_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=True)
    store = Column(String(100), nullable=False)
    total_amount = Column(Float, nullable=False)
    purchase_date = Column(DateTime(timezone=True), nullable=False)
    receipt_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="purchases")
    deal = relationship("Deal")

class ShoppingPreference(Base):
    __tablename__ = "shopping_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    preferred_stores = Column(JSON, nullable=True)  # List of preferred stores
    excluded_stores = Column(JSON, nullable=True)  # List of excluded stores
    preferred_categories = Column(JSON, nullable=True)  # List of preferred categories
    min_discount_percentage = Column(Float, nullable=True)
    max_price_threshold = Column(Float, nullable=True)
    notification_email = Column(String(255), nullable=True)
    notification_mobile = Column(String(20), nullable=True)
    notification_preferences = Column(JSON, nullable=True)  # Notification settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="shopping_preferences") 