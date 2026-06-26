from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Product:
    id: str
    name: str
    description: str
    price: float
    image_url: str
    category: str
    featured: bool = False
    stock: int = 0
    details: dict[str, Any] = field(default_factory=dict)
    translations: dict[str, str] | None = None
    created_date: datetime | None = None
    updated_date: datetime | None = None
    created_by_id: str | None = None
    is_sample: bool = False


@dataclass
class Order:
    id: str
    user_id: int
    product_id: str
    quantity: int
    status: str
    created_at: datetime
    updated_at: datetime
    shipping_address: dict[str, Any] | None = None
    payment_method: str | None = None
    payment_status: str | None = None
    payment_intent_id: str | None = None
    total_amount: float | None = None
    currency: str | None = None
    notes: str | None = None


@dataclass
class UserProfile:
    user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    created_at: datetime
    updated_at: datetime
    is_admin: bool = False
    is_blocked: bool = False
    shipping_address: dict[str, Any] | None = None
    payment_method: str | None = None
    last_interaction: datetime | None = None
    total_orders: int = 0
    total_spent: float = 0.0
    preferences: dict[str, Any] | None = None


@dataclass
class FollowUp:
    id: str
    user_id: int
    message: str
    scheduled_at: datetime
    sent_at: datetime | None = None
    status: str = "pending"
    retry_count: int = 0
    last_error: str | None = None


@dataclass
class Payment:
    id: str
    user_id: int
    order_id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    payment_intent_id: str | None = None
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class Notification:
    id: str
    user_id: int
    message: str
    created_at: datetime
    read_at: datetime | None = None
    type: str = "info"
    data: dict[str, Any] | None = None


@dataclass
class CartItem:
    product_id: str
    quantity: int
    price: float
    name: str
    image_url: str
    category: str
    details: dict[str, Any] | None = None
    translations: dict[str, str] | None = None


@dataclass
class Cart:
    user_id: int
    items: list[CartItem]
    created_at: datetime
    updated_at: datetime
    total_amount: float = 0.0
    currency: str = "EUR"