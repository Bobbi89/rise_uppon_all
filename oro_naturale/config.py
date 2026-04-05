from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    admin_chat_ids: set[int]
    products_csv: str
    data_dir: str
    free_shipping_min: float
    default_shipping: float
    b2b_discount: float
    stripe_secret_key: str
    stripe_currency: str
    followup_hours: float


def _parse_admin_ids(value: str) -> set[int]:
    ids: set[int] = set()
    for raw in value.split(","):
        raw = raw.strip()
        if raw.isdigit():
            ids.add(int(raw))
    return ids


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in .env")

    return Settings(
        telegram_bot_token=token,
        admin_chat_ids=_parse_admin_ids(os.getenv("ADMIN_CHAT_ID", "")),
        products_csv=os.getenv("PRODUCTS_CSV", "Product_export.csv"),
        data_dir=os.getenv("DATA_DIR", "data"),
        free_shipping_min=float(os.getenv("FREE_SHIPPING_MIN", "100")),
        default_shipping=float(os.getenv("DEFAULT_SHIPPING", "14")),
        b2b_discount=float(os.getenv("B2B_DISCOUNT", "15")),
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", "").strip(),
        stripe_currency=os.getenv("STRIPE_CURRENCY", "eur").strip().lower(),
        followup_hours=float(os.getenv("FOLLOWUP_HOURS", "24")),
    )
