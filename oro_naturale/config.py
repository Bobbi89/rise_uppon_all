# config.py
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carica le variabili dal file .env
load_dotenv()


@dataclass(slots=True)
class Settings:
    """Configurazioni globali del Bot caricate da environment."""
    
    # Telegram
    telegram_bot_token: str
    admin_chat_ids: set[int]
    
    # Filesystem e Dati
    products_csv: str
    data_dir: str
    
    # Regole di Spedizione e Sconti
    free_shipping_min: float  # Soglia per spedizione gratuita
    default_shipping: float   # Costo spedizione standard
    b2b_discount: float       # Sconto percentuale per clienti B2B
    
    # Pagamenti (Stripe)
    stripe_secret_key: str
    stripe_currency: str
    
    # Automazioni
    followup_hours: float     # Ore dopo le quale inviare un messaggio di follow-up


def _parse_admin_ids(value: str) -> set[int]:
    """Converte una stringa di ID separati da virgola in un set di interi."""
    ids: set[int] = set()
    for raw in value.split(","):
        raw = raw.strip()
        if raw.lstrip("-").isdigit():  # Supporta ID negativi se necessario
            ids.add(int(raw))
    return ids


def load_settings() -> Settings:
    """Carica le impostazioni dalle variabili d'ambiente."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in .env")

    return Settings(
        # Dati Bot
        telegram_bot_token=token,
        admin_chat_ids=_parse_admin_ids(os.getenv("ADMIN_CHAT_ID", "")),
        
        # Percorsi Dati
        products_csv=os.getenv("PRODUCTS_CSV", "Product_export.csv"),
        data_dir=os.getenv("DATA_DIR", "data"),
        
        # Spedizioni e Promozioni (Defaults adatti a negozio fisico)
        free_shipping_min=float(os.getenv("FREE_SHIPPING_MIN", "50.00")),
        default_shipping=float(os.getenv("DEFAULT_SHIPPING", "4.90")),
        b2b_discount=float(os.getenv("B2B_DISCOUNT", "15.0")),
        
        # Pagamenti
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", "").strip(),
        stripe_currency=os.getenv("STRIPE_CURRENCY", "eur").strip().lower(),
        
        # Follow-up ordini (es. 24h dopo l'acquisto per recensione/assistenza)
        followup_hours=float(os.getenv("FOLLOWUP_HOURS", "24")),
    )