from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import Settings
from .models import Product
from .storage import FileStore, load_products_json, save_products_json


@dataclass
class BotContext:
    settings: Settings
    store: FileStore
    products: list[Product] = field(default_factory=list)
    company: dict[str, Any] = field(default_factory=dict)
    payment_methods: list[str] = field(default_factory=list)
    custom_products: list[Product] = field(default_factory=list)
    customers: dict[str, Any] = field(default_factory=dict)
    faq: dict[str, str] = field(default_factory=dict)
    seasonal_promos: dict[str, str] = field(default_factory=dict)
    shipping_rules: dict[str, float] = field(default_factory=dict)

    def reload_products(self, products: list[Product]) -> None:
        self.products = products

    def refresh_from_store(self) -> None:
        self.company = self.store.load_json("company.json", {})
        self.payment_methods = self.store.load_json("payments_methods.json", [])
        self.custom_products = load_products_json(self.store.json_path("custom_products.json"))
        self.customers = self.store.load_json("customers.json", {})
        self.faq = self.store.load_json("faq.json", {})
        self.seasonal_promos = self.store.load_json("seasonal_promos.json", {})
        self.shipping_rules = self.store.load_json("shipping.json", {})

    def save_company(self) -> None:
        self.store.save_json("company.json", self.company)

    def save_payment_methods(self) -> None:
        self.store.save_json("payments_methods.json", self.payment_methods)

    def save_custom_products(self) -> None:
        save_products_json(self.store.json_path("custom_products.json"), self.custom_products)

    def save_customers(self) -> None:
        self.store.save_json("customers.json", self.customers)

    def save_faq(self) -> None:
        self.store.save_json("faq.json", self.faq)

    def save_seasonal_promos(self) -> None:
        self.store.save_json("seasonal_promos.json", self.seasonal_promos)

    def save_shipping(self) -> None:
        self.store.save_json("shipping.json", self.shipping_rules)