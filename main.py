from __future__ import annotations

import os
import psycopg2
import asyncio
import signal
import json

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import (
    BotCommand,
    MenuButtonCommands,
    MenuButtonWebApp,
    TelegramObject,
    WebAppInfo,
)
from aiogram.client.default import DefaultBotProperties

from oro_naturale.config import load_settings
from oro_naturale.context import BotContext
from oro_naturale.routers.admin import build_admin_router
from oro_naturale.routers.public import build_public_router
from oro_naturale.services import followup_worker
from oro_naturale.storage import FileStore, load_products_from_db
from oro_naturale.webserver import start_web_server


# Comandi mostrati nel menu "/" di Telegram
BOT_COMMANDS = [
    BotCommand(command="start",     description="🏠 Menu principale"),
    BotCommand(command="catalogo",  description="🛍️ Sfoglia il catalogo"),
    BotCommand(command="carrello",  description="🛒 Il tuo carrello"),
    BotCommand(command="ordini",    description="📦 I tuoi ordini"),
    BotCommand(command="spedizione", description="🚚 Info spedizione"),
    BotCommand(command="contatti",  description="📞 Contatti"),
]


async def setup_bot_menu(bot: Bot, webapp_url: str) -> None:
    """Imposta i comandi e il pulsante-menu (Mini App se disponibile via HTTPS)."""
    try:
        await bot.set_my_commands(BOT_COMMANDS)
    except Exception as e:
        print(f"⚠️ set_my_commands fallito: {e}")

    try:
        if webapp_url.startswith("https://"):
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="🌿 Negozio",
                    web_app=WebAppInfo(url=webapp_url),
                )
            )
            print(f"🟢 Pulsante Mini App impostato → {webapp_url}")
        else:
            await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
            print("ℹ️ WEBAPP_URL non HTTPS: pulsante-menu su comandi.")
    except Exception as e:
        print(f"⚠️ set_chat_menu_button fallito: {e}")


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


# ==========================================
# MIGRAZIONE prodotti da JSON a PostgreSQL
# ==========================================
def migrate_products():
    """
    Esegue la migrazione dei prodotti da products.json al database PostgreSQL.
    Viene chiamata all'avvio del bot.
    """
    try:
        DATABASE_URL = os.environ["DATABASE_URL"]
        JSON_PATH = "products.json"

        if not os.path.exists(JSON_PATH):
            print("❌ products.json non trovato. Migrazione saltata.")
            return

        with open(JSON_PATH, "r", encoding="utf-8") as f:
            products = json.load(f)

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        for p in products:
            # Usa name_it come name se presente, altrimenti usa una stringa vuota
            name = p.get("name_it") or ""
            description = p.get("description_it") or ""

            # Converte in tipi corretti (i campi possono essere str, int o bool)
            price = float(p.get("price") or 0)
            stock = int(p.get("stock") or 0)
            featured = str(p.get("featured", "false")).lower() == "true"
            is_sample = str(p.get("is_sample", "false")).lower() == "true"

            # Converti attributes in JSON string
            attributes = p.get("attributes")
            details_json = json.dumps(attributes) if attributes else None

            cur.execute("""
                INSERT INTO products (
                    id, name, description, price, image_url, category,
                    stock, featured, is_sample, details, translations,
                    created_date, updated_date, created_by_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    image_url = EXCLUDED.image_url,
                    category = EXCLUDED.category,
                    stock = EXCLUDED.stock,
                    featured = EXCLUDED.featured,
                    is_sample = EXCLUDED.is_sample,
                    details = EXCLUDED.details,
                    translations = EXCLUDED.translations,
                    created_date = EXCLUDED.created_date,
                    updated_date = EXCLUDED.updated_date,
                    created_by_id = EXCLUDED.created_by_id
            """, (
                p.get("id"),
                name,
                description,
                price,
                p.get("image_url"),
                p.get("category"),
                stock,
                featured,
                is_sample,
                details_json,
                None,
                None,
                None,
                None,
            ))

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Migrazione prodotti completata.")
    except Exception as e:
        print(f"❌ Errore durante la migrazione prodotti: {e}")


# ==========================================
# MIDDLEWARE DI RETRY PER TELEGRAM NETWORK ERRORS
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
            except TelegramNetworkError:
                if attempt == self.max_retries - 1:
                    raise  # ultimo tentativo, rilancio
                wait = self.base_delay * (2 ** attempt)  # backoff esponenziale
                print(f"[RetryTelegramMiddleware] TelegramNetworkError, ritento tra {wait}s...")
                await asyncio.sleep(wait)
        return None  # non dovrebbe mai arrivare qui


# ==========================================
# FUNZIONE PRINCIPALE
# ==========================================
async def main() -> None:
    # Piccolo delay per evitare conflitti con altre istanze
    await asyncio.sleep(2)

    # 1. Migrazione prodotti da JSON a DB
    print("🔄 Avvio migrazione prodotti da JSON a PostgreSQL...")
    migrate_products()

    # 2. Caricamento impostazioni e contesto
    settings = load_settings()
    store = FileStore(settings.data_dir)
    ctx = BotContext(settings=settings, store=store)
    ctx.refresh_from_store()

    # 3. Carica prodotti dal DB PostgreSQL
    db_products = load_products_from_db()
    ctx.reload_products(db_products + ctx.custom_products)
    print(f"📦 Caricati {len(db_products)} prodotti dal database.")

    # 4. Inizializzazione bot e dispatcher
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    # Middleware di retry per gestire disconnessioni Telegram
    dp.update.middleware(RetryTelegramMiddleware(max_retries=3, base_delay=1.0))

    dp.include_router(build_public_router(ctx))
    dp.include_router(build_admin_router(ctx))

    # Worker per followup e notifiche
    asyncio.create_task(followup_worker(bot, store, settings))

    # Web server della Mini App (se Railway/host fornisce una PORT)
    web_runner = None
    if settings.web_port:
        web_runner = await start_web_server(settings.web_port)
        print(f"🌐 Mini App in ascolto su porta {settings.web_port}")
    else:
        print("ℹ️ Nessuna PORT: la Mini App non viene servita da questo processo.")

    # Comandi + pulsante Mini App su Telegram
    await setup_bot_menu(bot, settings.webapp_url)

    # Gestione pulita dei segnali di shutdown
    async def shutdown():
        print("🛑 Chiusura pulita del bot...")
        if web_runner is not None:
            await web_runner.cleanup()
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

    # 5. Avvio polling
    print("🤖 Bot avviato. In ascolto su Telegram...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())