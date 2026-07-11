# ═══════════════════════════════════════════════════════════════════
#  Oro Naturale — Database (PostgreSQL)
#
#  Persistenza di clienti e ordini. Funzioni SINCRONE (psycopg2): l'API
#  async le richiama con asyncio.to_thread per non bloccare l'event loop.
#
#  DATABASE_URL è letta in modo lazy così i moduli si importano anche
#  senza database configurato (es. nei test che non toccano il DB).
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor

logger = logging.getLogger(__name__)


def _database_url(override: str | None = None) -> str:
    url = override or os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL non configurata")
    return url


@contextmanager
def _conn(database_url: str | None = None) -> Iterator[Any]:
    """Connessione psycopg2 con commit/rollback automatici."""
    conn = psycopg2.connect(_database_url(database_url), cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════
#  SCHEMA
# ═══════════════════════════════════════════════════════════════════

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    user_id     BIGINT PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    last_name   TEXT,
    phone       TEXT,
    address     TEXT,
    city        TEXT,
    zip         TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
    id                TEXT PRIMARY KEY,
    user_id           BIGINT,
    username          TEXT,
    items             JSONB NOT NULL DEFAULT '[]'::jsonb,
    subtotal          NUMERIC(10,2) NOT NULL DEFAULT 0,
    shipping          NUMERIC(10,2) NOT NULL DEFAULT 0,
    total             NUMERIC(10,2) NOT NULL DEFAULT 0,
    currency          TEXT NOT NULL DEFAULT 'EUR',
    status            TEXT NOT NULL DEFAULT 'pending',
    payment_method    TEXT,
    payment_provider  TEXT,
    revolut_order_id  TEXT,
    shipping_name     TEXT,
    shipping_phone    TEXT,
    shipping_address  TEXT,
    shipping_city     TEXT,
    shipping_zip      TEXT,
    shipping_notes    TEXT,
    tracking_carrier  TEXT,
    tracking_code     TEXT,
    tracking_url      TEXT,
    tracking_status   TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at           TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders (user_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at DESC);
"""


def init_schema(database_url: str | None = None) -> None:
    """Crea le tabelle customers/orders se non esistono."""
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
    logger.info("Schema DB (customers/orders) verificato/creato.")


# ═══════════════════════════════════════════════════════════════════
#  CUSTOMERS
# ═══════════════════════════════════════════════════════════════════

def upsert_customer(
    user_id: int,
    *,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    city: str | None = None,
    zip_code: str | None = None,
    database_url: str | None = None,
) -> None:
    """Crea/aggiorna il profilo cliente. I campi None non sovrascrivono valori esistenti."""
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO customers (user_id, username, first_name, last_name, phone, address, city, zip)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username   = COALESCE(EXCLUDED.username,   customers.username),
                    first_name = COALESCE(EXCLUDED.first_name, customers.first_name),
                    last_name  = COALESCE(EXCLUDED.last_name,  customers.last_name),
                    phone      = COALESCE(EXCLUDED.phone,      customers.phone),
                    address    = COALESCE(EXCLUDED.address,    customers.address),
                    city       = COALESCE(EXCLUDED.city,       customers.city),
                    zip        = COALESCE(EXCLUDED.zip,        customers.zip),
                    updated_at = now()
                """,
                (user_id, username, first_name, last_name, phone, address, city, zip_code),
            )


def get_customer(user_id: int, database_url: str | None = None) -> Optional[dict]:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM customers WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return _serialize(row) if row else None


# ═══════════════════════════════════════════════════════════════════
#  ORDERS
# ═══════════════════════════════════════════════════════════════════

def create_order(order: dict, database_url: str | None = None) -> None:
    """Inserisce un ordine. `order['items']` è una lista di dict."""
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO orders (
                    id, user_id, username, items, subtotal, shipping, total, currency,
                    status, payment_method, payment_provider, revolut_order_id,
                    shipping_name, shipping_phone, shipping_address, shipping_city,
                    shipping_zip, shipping_notes
                ) VALUES (
                    %(id)s, %(user_id)s, %(username)s, %(items)s, %(subtotal)s, %(shipping)s,
                    %(total)s, %(currency)s, %(status)s, %(payment_method)s, %(payment_provider)s,
                    %(revolut_order_id)s, %(shipping_name)s, %(shipping_phone)s, %(shipping_address)s,
                    %(shipping_city)s, %(shipping_zip)s, %(shipping_notes)s
                )
                """,
                {
                    "id": order["id"],
                    "user_id": order.get("user_id"),
                    "username": order.get("username"),
                    "items": Json(order.get("items", [])),
                    "subtotal": order.get("subtotal", 0),
                    "shipping": order.get("shipping", 0),
                    "total": order.get("total", 0),
                    "currency": order.get("currency", "EUR"),
                    "status": order.get("status", "pending"),
                    "payment_method": order.get("payment_method"),
                    "payment_provider": order.get("payment_provider"),
                    "revolut_order_id": order.get("revolut_order_id"),
                    "shipping_name": order.get("shipping_name"),
                    "shipping_phone": order.get("shipping_phone"),
                    "shipping_address": order.get("shipping_address"),
                    "shipping_city": order.get("shipping_city"),
                    "shipping_zip": order.get("shipping_zip"),
                    "shipping_notes": order.get("shipping_notes"),
                },
            )


def get_order(order_id: str, database_url: str | None = None) -> Optional[dict]:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            row = cur.fetchone()
            return _serialize(row) if row else None


def list_user_orders(user_id: int, limit: int = 50, database_url: str | None = None) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                (user_id, limit),
            )
            return [_serialize(r) for r in cur.fetchall()]


def list_all_orders(
    limit: int = 100,
    *,
    exclude_pending: bool = True,
    database_url: str | None = None,
) -> list[dict]:
    """
    Elenco ordini per l'admin. Di default esclude i 'pending' (non pagati):
    l'admin vede solo gli ordini effettivamente pagati.
    """
    where = "WHERE status <> 'pending'" if exclude_pending else ""
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM orders {where} ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return [_serialize(r) for r in cur.fetchall()]


def delete_pending_orders(user_id: int, database_url: str | None = None) -> int:
    """Elimina gli ordini non pagati (pending) dell'utente. Ritorna quanti ne ha rimossi."""
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM orders WHERE user_id = %s AND status = 'pending'",
                (user_id,),
            )
            return cur.rowcount


def update_order_status(
    order_id: str,
    status: str,
    *,
    mark_paid: bool = False,
    payment_method: str | None = None,
    revolut_order_id: str | None = None,
    database_url: str | None = None,
) -> Optional[dict]:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orders SET
                    status = %s,
                    payment_method = COALESCE(%s, payment_method),
                    revolut_order_id = COALESCE(%s, revolut_order_id),
                    paid_at = CASE WHEN %s THEN now() ELSE paid_at END,
                    updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (status, payment_method, revolut_order_id, mark_paid, order_id),
            )
            row = cur.fetchone()
            return _serialize(row) if row else None


def set_tracking(
    order_id: str,
    *,
    carrier: str,
    code: str,
    url: str | None = None,
    status: str = "shipped",
    database_url: str | None = None,
) -> Optional[dict]:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orders SET
                    tracking_carrier = %s,
                    tracking_code = %s,
                    tracking_url = %s,
                    tracking_status = %s,
                    status = %s,
                    updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (carrier, code, url, status, status, order_id),
            )
            row = cur.fetchone()
            return _serialize(row) if row else None


# ═══════════════════════════════════════════════════════════════════
#  SERIALIZZAZIONE (JSON-safe per l'API)
# ═══════════════════════════════════════════════════════════════════

def _serialize(row: Any) -> dict:
    """Converte una riga in dict JSON-safe (Decimal→float, datetime→ISO)."""
    from datetime import datetime
    from decimal import Decimal

    out: dict[str, Any] = {}
    for key, value in dict(row).items():
        if isinstance(value, Decimal):
            out[key] = float(value)
        elif isinstance(value, datetime):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out
