from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Iterable

from .models import Product


CATEGORY_LABELS = {
    "extra_virgin_olive_oil": "Olio Extravergine di Oliva",
    "flavored_oil": "Oli Aromatizzati",
    "wine": "Vini",
    "cosmetics": "Cosmetici all'olio d'oliva",
    "gift_box": "Confezioni Regalo",
    "food": "Gourmet",
}


def category_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def group_by_category(products: Iterable[Product]) -> dict[str, list[Product]]:
    grouped: dict[str, list[Product]] = {}
    for product in products:
        grouped.setdefault(product.category or "other", []).append(product)
    return grouped


def product_price_value(product: Product) -> float | None:
    if not product.price:
        return None
    try:
        return float(product.price.replace(",", "."))
    except ValueError:
        return None


def format_product(product: Product) -> str:
    price = f"EUR {product.price}" if product.price else "Prezzo su richiesta"
    description = product.description or "Descrizione non disponibile."
    return f"<b>{product.name}</b>\n{description}\n💰 {price}"


def format_products(items: Iterable[Product], limit: int = 12) -> str:
    lines = []
    for product in list(items)[:limit]:
        price = f"EUR {product.price}" if product.price else "Prezzo su richiesta"
        lines.append(f"- {product.name} - {price}")
    return "\n".join(lines) if lines else "Nessun prodotto disponibile."


def find_products(products: Iterable[Product], query: str) -> list[Product]:
    q = query.lower().strip()
    return [p for p in products if q in p.name.lower()]


def recommendations_for(products: list[Product], preference: str | None, fmt: str | None) -> list[Product]:
    items = products
    if preference == "moraiolo":
        items = [p for p in items if "moraiolo" in p.name.lower()]
    elif preference == "frantoio":
        items = [p for p in items if "frantoio" in p.name.lower()]
    if fmt:
        items = [p for p in items if fmt in p.name.lower()]
    return items[:5]


def calculate_cart_total(products: list[Product], cart: dict[str, int]) -> float:
    total = 0.0
    product_index = {product_key(p): p for p in products}
    for key, qty in cart.items():
        product = product_index.get(key)
        if not product:
            continue
        price = product_price_value(product)
        if price is not None:
            total += price * qty
    return total


def export_product(product: Product) -> dict[str, str]:
    return asdict(product)


def product_key(product: Product) -> str:
    return hashlib.sha1(product.name.encode("utf-8")).hexdigest()[:10]
