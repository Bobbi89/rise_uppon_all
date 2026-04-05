from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher

from oro_naturale.config import load_settings
from oro_naturale.context import BotContext
from oro_naturale.routers.admin import build_admin_router
from oro_naturale.routers.public import build_public_router
from oro_naturale.services import followup_worker
from oro_naturale.storage import FileStore, load_products_from_csv


async def main() -> None:
    settings = load_settings()
    store = FileStore(settings.data_dir)
    ctx = BotContext(settings=settings, store=store)
    ctx.refresh_from_store()
    ctx.reload_products(load_products_from_csv(settings.products_csv) + ctx.custom_products)

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(build_public_router(ctx))
    dp.include_router(build_admin_router(ctx))

    asyncio.create_task(followup_worker(bot, store, settings))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
