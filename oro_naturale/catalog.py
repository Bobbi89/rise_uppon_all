# catalog.py
from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Iterable

from .models import Product


# ═══════════════════════════════════════════════════════════════════
#  COSTANTI CATEGORIE
# ═══════════════════════════════════════════════════════════════════

CATEGORY_LABELS = {
    "extra_virgin_olive_oil": "Olio Extravergine di Oliva",
    "flavored_oils": "Oli Aromatizzati",
    "wines": "Vini",
    "cosmetics": "Cosmetici all'olio d'oliva",
    "gift_boxes": "Confezioni Regalo",
    "food": "Gourmet",
}


# ═══════════════════════════════════════════════════════════════════
#  HELPER CATEGORIE
# ═══════════════════════════════════════════════════════════════════

def category_label(category: str) -> str:
    """Restituisce l'etichetta leggibile della categoria."""
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def group_by_category(products: Iterable[Product]) -> dict[str, list[Product]]:
    """Raggruppa una lista di prodotti per categoria."""
    grouped: dict[str, list[Product]] = {}
    for product in products:
        cat = product.category or "other"
        grouped.setdefault(cat, []).append(product)
    return grouped


# ═══════════════════════════════════════════════════════════════════
#  HELPER PREZZI E CHIAVI
# ═══════════════════════════════════════════════════════════════════

def product_price_value(product: Product) -> float | None:
    """Converte il prezzo in float, gestendo virgole e valori vuoti."""
    if not product.price:
        return None
    try:
        cleaned_price = str(product.price).replace(",", ".").strip()
        return float(cleaned_price)
    except ValueError:
        return None


def product_key(product: Product) -> str:
    """Genera una chiave hash univoca per il prodotto basata sul nome."""
    return hashlib.sha1(product.name.encode("utf-8")).hexdigest()[:10]


# ═══════════════════════════════════════════════════════════════════
#  FORMATTAZIONE TESTO
# ═══════════════════════════════════════════════════════════════════

def format_product(product: Product) -> str:
    """Formatta un singolo prodotto per l'invio in chat (testo)."""
    price = f"EUR {product.price}" if product.price else "Prezzo su richiesta"
    description = product.description or "Descrizione non disponibile."
    return f"<b>{product.name}</b>\n{description}\n\U0001f4b0 {price}"


def format_products(items: Iterable[Product], limit: int = 12) -> str:
    """Formatta una lista di prodotti in un unico testo (max 12)."""
    lines = []
    for product in list(items)[:limit]:
        price = f"EUR {product.price}" if product.price else "Prezzo su richiesta"
        lines.append(f"- {product.name} - {price}")
    return "\n".join(lines) if lines else "Nessun prodotto disponibile."


# ═══════════════════════════════════════════════════════════════════
#  RICERCA E FILTRI
# ═══════════════════════════════════════════════════════════════════

def find_products(products: Iterable[Product], query: str) -> list[Product]:
    """Cerca prodotti in base a una query testuale (case-insensitive)."""
    q = query.lower().strip()
    if not q:
        return []
    return [p for p in products if q in p.name.lower()]


def recommendations_for(products: list[Product], preference: str | None, fmt: str | None) -> list[Product]:
    """Filtra prodotti per raccomandazioni personalizzate (es. tipi di oliva)."""
    items = products
    if preference == "moraiolo":
        items = [p for p in items if "moraiolo" in p.name.lower()]
    elif preference == "frantoio":
        items = [p for p in items if "frantoio" in p.name.lower()]
    
    if fmt:
        items = [p for p in items if fmt in p.name.lower()]
        
    return items[:5]


# ═══════════════════════════════════════════════════════════════════
#  CARRELLO E TOTALI
# ═══════════════════════════════════════════════════════════════════

def calculate_cart_total(products: list[Product], cart: dict[str, int]) -> float:
    """Calcola il totale monetario del carrello basato sui prodotti reali."""
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


# ═══════════════════════════════════════════════════════════════════
#  ESPORTAZIONE
# ═══════════════════════════════════════════════════════════════════

def export_product(product: Product) -> dict[str, str]:
    """Esporta il prodotto in dizionario per salvataggio JSON."""
    data = asdict(product)
    if 'details' not in data or data['details'] is None:
        data['details'] = {}
    return data