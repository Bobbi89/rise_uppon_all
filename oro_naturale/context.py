# oro_naturale/context.py
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

    # ── Stato checkout per utente ─────────────────────────────────
    # Struttura per utente:
    #   checkout_state[user_id] = {
    #       "shipping": "home" | "pickup",
    #       "shipping_cost": float,
    #       "coupon": str | None,
    #       "discount": float,
    #       "total": float,
    #   }
    checkout_state: dict[str, dict[str, Any]] = field(default_factory=dict)

    # ── Preferiti per utente ──────────────────────────────────────
    # favorites[user_id] = [product_key, ...]
    favorites: dict[str, list[str]] = field(default_factory=dict)

    # ── Storico recensioni ────────────────────────────────────────
    # reviews[order_id] = {"rating": int, "user_id": int}
    reviews: dict[str, dict[str, Any]] = field(default_factory=dict)

    # ─────────────────────────────────────────────────────────────
    #  Prodotti
    # ─────────────────────────────────────────────────────────────

    def reload_products(self, products: list[Product]) -> None:
        self.products = products

    # ─────────────────────────────────────────────────────────────
    #  Bootstrap da FileStore
    # ─────────────────────────────────────────────────────────────

    def refresh_from_store(self) -> None:
        self.company         = self.store.load_json("company.json", {})
        self.payment_methods = self.store.load_json("payments_methods.json", [])
        self.custom_products = load_products_json(self.store.json_path("custom_products.json"))
        self.customers       = self.store.load_json("customers.json", {})
        self.faq             = self.store.load_json("faq.json", {})
        self.seasonal_promos = self.store.load_json("seasonal_promos.json", {})
        self.shipping_rules  = self.store.load_json("shipping.json", {})
        self.favorites       = self.store.load_json("favorites.json", {})
        self.reviews         = self.store.load_json("reviews.json", {})
        # checkout_state è in-memory: non viene persistito tra riavvii

    # ─────────────────────────────────────────────────────────────
    #  Persist helpers
    # ─────────────────────────────────────────────────────────────

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

    def save_favorites(self) -> None:
        self.store.save_json("favorites.json", self.favorites)

    def save_reviews(self) -> None:
        self.store.save_json("reviews.json", self.reviews)

    # ─────────────────────────────────────────────────────────────
    #  Checkout state helpers
    # ─────────────────────────────────────────────────────────────

    def get_checkout(self, user_id: int) -> dict[str, Any]:
        """Restituisce lo stato checkout corrente per l'utente."""
        return self.checkout_state.get(str(user_id), {})

    def set_checkout(self, user_id: int, data: dict[str, Any]) -> None:
        """Aggiorna lo stato checkout per l'utente."""
        self.checkout_state[str(user_id)] = data

    def clear_checkout(self, user_id: int) -> None:
        """Pulisce lo stato checkout dopo pagamento confermato."""
        self.checkout_state.pop(str(user_id), None)

    # ─────────────────────────────────────────────────────────────
    #  Favorites helpers
    # ─────────────────────────────────────────────────────────────

    def get_favorites(self, user_id: int) -> list[str]:
        return self.favorites.get(str(user_id), [])

    def toggle_favorite(self, user_id: int, product_key: str) -> bool:
        """
        Aggiunge/rimuove il prodotto dai preferiti.
        Restituisce True se ora è nei preferiti, False se rimosso.
        """
        key = str(user_id)
        favs = self.favorites.get(key, [])
        if product_key in favs:
            favs.remove(product_key)
            added = False
        else:
            favs.append(product_key)
            added = True
        self.favorites[key] = favs
        self.save_favorites()
        return added

    def is_favorite(self, user_id: int, product_key: str) -> bool:
        return product_key in self.get_favorites(user_id)

    # ─────────────────────────────────────────────────────────────
    #  Reviews helpers
    # ─────────────────────────────────────────────────────────────

    def save_review(self, order_id: str, user_id: int, rating: int) -> None:
        self.reviews[order_id] = {"rating": rating, "user_id": user_id}
        self.save_reviews()

    def avg_rating(self) -> float:
        """Media dei rating su tutti gli ordini recensiti."""
        if not self.reviews:
            return 0.0
        return sum(r["rating"] for r in self.reviews.values()) / len(self.reviews)

    # ─────────────────────────────────────────────────────────────
    #  Statistiche admin
    # ─────────────────────────────────────────────────────────────

    def pending_orders_count(self) -> int:
        """Conta ordini con status pending su tutti i clienti."""
        count = 0
        for record in self.customers.values():
            for order in record.get("orders", []):
                if order.get("status", "pending") == "pending":
                    count += 1
        return count

    def total_customers_count(self) -> int:
        return len(self.customers)

    def active_products_count(self) -> int:
        return len(self.products)