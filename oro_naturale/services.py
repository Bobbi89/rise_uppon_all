from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Optional

from aiogram.types import Message

try:
    import stripe  # type: ignore
except Exception:
    stripe = None

from .catalog import calculate_cart_total, product_price_value
from .config import Settings
from .models import Product
from .storage import FileStore


@dataclass(slots=True)
class OrderResult:
    order_id: str
    subtotal: float
    shipping: float
    total: float
    country: str | None
    summary: str


def is_admin_user(user_id: Optional[int], settings: Settings) -> bool:
    return bool(user_id and user_id in settings.admin_chat_ids)


def detect_language(text: str) -> Optional[str]:
    t = text.lower()
    if any(word in t for word in ["hallo", "bestellung", "versand", "zahlung"]):
        return "de"
    if any(word in t for word in ["hello", "order", "shipping", "payment"]):
        return "en"
    if any(word in t for word in ["ciao", "ordine", "spedizione", "pagamento"]):
        return "it"
    return None


def detect_b2b(text: str) -> bool:
    t = text.lower()
    return any(word in t for word in ["ristoratore", "ristorante", "partita iva", "p.iva", "azienda", "fornitura"])


def detect_preference(text: str) -> Optional[str]:
    t = text.lower()
    if "moraiolo" in t:
        return "moraiolo"
    if "frantoio" in t:
        return "frantoio"
    return None


def detect_format(text: str) -> Optional[str]:
    t = text.lower()
    if "5l" in t or "5 l" in t:
        return "5"
    if "500" in t:
        return "500"
    if "250" in t:
        return "250"
    return None


def parse_total(text: str) -> Optional[float]:
    match = re.search(r"(totale|total|gesamt)[^0-9]*([0-9]+([.,][0-9]+)?)", text, re.I)
    if not match:
        match = re.search(r"([0-9]+([.,][0-9]+)?)\s*(eur|€)", text, re.I)
    if not match:
        return None
    try:
        return float(match.group(2).replace(",", "."))
    except ValueError:
        return None


def parse_country(text: str, default: str = "IT") -> str:
    match = re.search(r"(paese|country|land)[^A-Za-z]*([A-Za-z]{2,})", text, re.I)
    if match:
        return match.group(2).upper()
    upper = text.upper()
    for code in ["IT", "DE", "FR", "ES", "NL", "BE", "AT"]:
        if code in upper:
            return code
    return default


def shipping_cost(country: str, subtotal: float, settings: Settings, rules: dict[str, float]) -> float:
    if subtotal >= settings.free_shipping_min:
        return 0.0
    country = country.upper()
    return rules.get(country, settings.default_shipping)


def create_stripe_link(amount: float, settings: Settings, description: str) -> Optional[str]:
    if not settings.stripe_secret_key or stripe is None:
        return None
    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": settings.stripe_currency,
                    "product_data": {"name": description},
                    "unit_amount": int(round(amount * 100)),
                },
                "quantity": 1,
            }
        ],
        success_url="https://biomarketshop.com",
        cancel_url="https://biomarketshop.com",
    )
    return session.url


def format_company(company: dict[str, Any]) -> str:
    if not company:
        return "Contatti non disponibili. Scrivi all'admin."
    lines = []
    for key in ["name", "website", "email", "phone", "vat", "hours", "address"]:
        value = company.get(key)
        if value:
            label = "P.IVA" if key == "vat" else key.title()
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def format_payments(methods: list[str], settings: Settings) -> str:
    items = list(methods)
    if settings.stripe_secret_key:
        items.append("Carta (Stripe)")
    if not items:
        return "Metodi di pagamento non disponibili."
    return "Metodi di pagamento:\n" + "\n".join(f"- {m}" for m in items)


def recommend_upsell(products: list[Product], subtotal: float, settings: Settings) -> list[Product]:
    gap = settings.free_shipping_min - subtotal
    if gap <= 0:
        return []
    candidates: list[tuple[Product, float]] = []
    for product in products:
        price = product_price_value(product)
        if price is not None:
            candidates.append((product, price))
    candidates.sort(key=lambda item: item[1])
    picks: list[Product] = []
    for product, price in candidates:
        if price <= gap + 5:
            picks.append(product)
        if len(picks) >= 3:
            break
    return picks


def process_order_payload(
    *,
    message: Message,
    store: FileStore,
    products: list[Product],
    settings: Settings,
    cart: dict[str, int],
    customer: dict[str, Any],
    order_text: str,
    shipping_rules: dict[str, float],
) -> OrderResult | None:
    subtotal = parse_total(order_text) or calculate_cart_total(products, cart)
    if subtotal <= 0:
        return None

    country = parse_country(order_text)
    shipping = shipping_cost(country, subtotal, settings, shipping_rules)
    total = subtotal + shipping
    if customer.get("type") == "b2b":
        subtotal = subtotal * (1 - settings.b2b_discount / 100.0)
        total = subtotal + shipping

    order_id = f"ON{int(time.time())}"
    payload = {
        "order_id": order_id,
        "ts": int(time.time()),
        "user_id": message.from_user.id if message.from_user else None,
        "username": message.from_user.username if message.from_user else None,
        "chat_id": message.chat.id,
        "details": order_text,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
        "country": country,
    }
    store.append_jsonl("orders.jsonl", payload)

    lines = [
        f"Ordine ricevuto: {order_id}",
        f"Sottototale: EUR {subtotal:.2f}",
        f"Spedizione ({country}): EUR {shipping:.2f}",
        f"Totale finale: EUR {total:.2f}",
    ]
    return OrderResult(order_id, subtotal, shipping, total, country, "\n".join(lines))


async def followup_worker(bot, store: FileStore, settings: Settings) -> None:
    while True:
        await asyncio.sleep(300)
        now = int(time.time())
        customers = store.load_json("customers.json", {})
        changed = False
        for user_id, record in list(customers.items()):
            next_followup = record.get("next_followup")
            if not next_followup or record.get("followup_sent"):
                continue
            if record.get("stage") not in {"proposal_sent", "payment_pending"}:
                continue
            if now >= int(next_followup):
                chat_id = record.get("chat_id")
                if chat_id:
                    try:
                        await bot.send_message(
                            int(chat_id),
                            "Ti ricontatto per il tuo ordine. Se vuoi, posso chiudere il checkout adesso.",
                        )
                    except Exception:
                        pass
                record["followup_sent"] = True
                customers[user_id] = record
                changed = True
        if changed:
            store.save_json("customers.json", customers)
