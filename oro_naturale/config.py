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

    # Pagamenti (Revolut Merchant API)
    revolut_public_key: str   # chiave pubblica (client-side RevolutCheckout)
    revolut_secret_key: str   # chiave segreta (server-side, crea ordini)
    revolut_mode: str         # "sandbox" | "prod"
    revolut_api_version: str

    # Pagamenti (PayPal — manuale: pagamento all'email del negozio)
    paypal_email: str         # email PayPal su cui ricevere i pagamenti
    paypal_me: str            # link PayPal.me opzionale (es. paypal.me/nome)

    # Contatti del negozio (mostrati in Contatti/Supporto/Negozio)
    shop_phone: str
    shop_email: str
    shop_address: str

    # Automazioni
    followup_hours: float     # Ore dopo le quale inviare un messaggio di follow-up

    # Mini App Telegram (webapp del marketplace)
    webapp_url: str           # URL HTTPS della mini app; vuoto = pulsante nascosto
    web_port: int | None      # Porta HTTP su cui servire la mini app (Railway $PORT)


def _parse_admin_ids(value: str) -> set[int]:
    """Converte una stringa di ID separati da virgola in un set di interi."""
    ids: set[int] = set()
    for raw in value.split(","):
        raw = raw.strip()
        if raw.lstrip("-").isdigit():  # Supporta ID negativi se necessario
            ids.add(int(raw))
    return ids


def _resolve_webapp_url() -> str:
    """
    URL pubblico della Mini App.

    Priorità:
      1. WEBAPP_URL esplicita (qualunque hosting)
      2. dominio pubblico Railway del servizio (RAILWAY_PUBLIC_DOMAIN),
         così la mini app servita dallo stesso processo è raggiungibile
         senza configurazione manuale.
    """
    explicit = os.getenv("WEBAPP_URL", "").strip()
    if explicit:
        return _normalize_https(explicit)

    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        return _normalize_https(railway_domain)

    return ""


def _normalize_https(url: str) -> str:
    """
    Normalizza un URL/dominio a forma https:// (Telegram accetta solo HTTPS
    per i pulsanti Web App). Aggiunge lo schema se manca, forza http→https,
    e rimuove lo slash finale.
    """
    url = url.strip().rstrip("/")
    if not url:
        return ""
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    elif not url.startswith("https://"):
        url = "https://" + url
    return url


def _resolve_web_port() -> int | None:
    """Porta HTTP per servire la mini app. Railway inietta PORT automaticamente."""
    raw = os.getenv("PORT", "").strip()
    if raw.isdigit():
        return int(raw)
    return None


def _env_any(*names: str, default: str = "") -> str:
    """Primo valore non vuoto tra più possibili nomi di variabile (case varianti)."""
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return default


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
        
        # Spedizioni (allineate a biomarketshop.com: gratis da 69€, standard EU 10,40€)
        free_shipping_min=float(os.getenv("FREE_SHIPPING_MIN", "69.00")),
        default_shipping=float(os.getenv("DEFAULT_SHIPPING", "10.40")),
        b2b_discount=float(os.getenv("B2B_DISCOUNT", "15.0")),
        
        # Pagamenti
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", "").strip(),
        stripe_currency=os.getenv("STRIPE_CURRENCY", "eur").strip().lower(),

        # Revolut (accetta più varianti di nome per le chiavi)
        revolut_public_key=_env_any(
            "REVOLUT_PUBLIC_API", "Revolut_public_api", "REVOLUT_PUBLIC_KEY"
        ),
        revolut_secret_key=_env_any(
            "REVOLUT_SECRET_API", "revolut_secret_api", "REVOLUT_SECRET_KEY"
        ),
        revolut_mode=(_env_any("REVOLUT_MODE", default="sandbox").lower()),
        revolut_api_version=_env_any("REVOLUT_API_VERSION", default="2024-09-01"),

        # PayPal (email del negozio per pagamenti manuali)
        paypal_email=_env_any("PAYPAL_EMAIL", "PAYPAL_ACCOUNT"),
        paypal_me=_env_any("PAYPAL_ME"),

        # Contatti negozio
        shop_phone=_env_any("SHOP_PHONE"),
        shop_email=_env_any("SHOP_EMAIL"),
        shop_address=_env_any("SHOP_ADDRESS", default="Via Ponte Vecchio 3, Niccone (PG)"),
        
        # Follow-up ordini (es. 24h dopo l'acquisto per recensione/assistenza)
        followup_hours=float(os.getenv("FOLLOWUP_HOURS", "24")),

        # Mini App
        webapp_url=_resolve_webapp_url(),
        web_port=_resolve_web_port(),
    )