from __future__ import annotations

import os
import psycopg2
import asyncio

from aiogram import Bot, Dispatcher

from oro_naturale.config import load_settings
from oro_naturale.context import BotContext
from oro_naturale.routers.admin import build_admin_router
from oro_naturale.routers.public import build_public_router
from oro_naturale.services import followup_worker
from oro_naturale.storage import FileStore, load_products_from_db


# ==========================================
# INIZIALIZZAZIONE DATABASE (Esegue subito all'avvio)
# ==========================================
print("Avvio: Controllo della tabella products nel database...")
try:
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                image_url TEXT,
                category TEXT,
                stock INTEGER DEFAULT 0,
                featured BOOLEAN DEFAULT FALSE,
                is_sample BOOLEAN DEFAULT FALSE,
                details JSONB,
                translations JSONB,
                created_date TIMESTAMPTZ,
                updated_date TIMESTAMPTZ,
                created_by_id TEXT
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ SUCCESSO: Tabella 'products' verificata/creata.")
    else:
        print("⚠️ ATTENZIONE: Variabile DATABASE_URL non trovata!")
except Exception as e:
    print(f"❌ ERRORE IMPREVISTO nella creazione della tabella: {e}")
# ==========================================


async def main() -> None:
    settings = load_settings()
    store = FileStore(settings.data_dir)
    ctx = BotContext(settings=settings, store=store)
    ctx.refresh_from_store()
    # Ora carica i prodotti dal DB PostgreSQL
    ctx.reload_products(load_products_from_db() + ctx.custom_products)

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(build_public_router(ctx))
    dp.include_router(build_admin_router(ctx))

    asyncio.create_task(followup_worker(bot, store, settings))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())