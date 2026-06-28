from __future__ import annotations

import os
import psycopg2
import asyncio
import signal

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import TelegramObject
from aiogram.client.default import DefaultBotProperties

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


class RetryTelegramMiddleware:
    """
    Middleware che ritenta automaticamente le chiamate Telegram
    in caso di TelegramNetworkError (ServerDisconnectedError, Connection reset by peer).
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def __call__(self, handler, event: TelegramObject, data: dict):
        for attempt in range(self.max_retries):
            try:
                return await handler(event, data)
            except TelegramNetworkError as e:
                if attempt == self.max_retries - 1:
                    raise  # ultimo tentativo, rilancio
                wait = self.base_delay * (2 ** attempt)  # backoff esponenziale
                print(f"[RetryTelegramMiddleware] TelegramNetworkError, ritento tra {wait}s...")
                await asyncio.sleep(wait)
        return None  # non dovrebbe mai arrivare qui


async def main() -> None:
    settings = load_settings()
    store = FileStore(settings.data_dir)
    ctx = BotContext(settings=settings, store=store)
    ctx.refresh_from_store()
    # Ora carica i prodotti dal DB PostgreSQL
    ctx.reload_products(load_products_from_db() + ctx.custom_products)

    # Usa DefaultBotProperties per gestire timeout e sessioni
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(
            parse_mode="HTML",
            # timeout ragionevoli per Railway
            read_timeout=30.0,
            write_timeout=30.0,
            connect_timeout=10.0,
        )
    )
    dp = Dispatcher()

    # Aggiungi middleware di retry
    dp.update.middleware(RetryTelegramMiddleware(max_retries=3, base_delay=1.0))

    dp.include_router(build_public_router(ctx))
    dp.include_router(build_admin_router(ctx))

    asyncio.create_task(followup_worker(bot, store, settings))

    # Gestione pulita dei segnali di shutdown
    async def shutdown():
        print("🛑 Chiusura pulita del bot...")
        await dp.storage.close()
        await bot.session.close()

    def signal_handler(sig):
        print(f"Ricevuto segnale {sig}, shutdown...")
        asyncio.create_task(shutdown())

    try:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, lambda: signal_handler(signal.SIGINT))
        loop.add_signal_handler(signal.SIGTERM, lambda: signal_handler(signal.SIGTERM))
    except NotImplementedError:
        # Windows non supporta add_signal_handler
        pass

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())