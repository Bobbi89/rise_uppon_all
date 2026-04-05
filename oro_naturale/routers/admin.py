from __future__ import annotations

import json
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..catalog import format_products, load_products_from_csv
from ..context import BotContext
from ..models import Product
from ..services import format_company, format_payments, is_admin_user
from ..storage import save_products_json


def build_admin_router(ctx: BotContext) -> Router:
    router = Router()

    def admin_only(message: Message) -> bool:
        return is_admin_user(message.from_user.id if message.from_user else None, ctx.settings)

    @router.message(Command("admin"))
    async def admin_help(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        await message.answer(
            "Admin:\n"
            "- /orders ultimi ordini\n"
            "- /payments ultimi pagamenti\n"
            "- /shipping_set <PAESE> <costo>\n"
            "- /shipping_list\n"
            "- /product_add <nome>|<prezzo>|<categoria>|<descrizione>\n"
            "- /product_del <nome>\n"
            "- /company_set <campo>|<valore>\n"
            "- /company_view\n"
            "- /payment_add <metodo>\n"
            "- /payment_del <metodo>\n"
            "- /payment_list\n"
            "- /faq_add <keyword>|<risposta>\n"
            "- /faq_del <keyword>\n"
            "- /faq_list\n"
            "- /crypto_set <network>|<address>\n"
            "- /crypto_list\n"
            "- /promo_set <stagione>|<testo>\n"
            "- /checkout <importo> [descrizione]"
        )

    @router.message(Command("orders"))
    async def orders(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        items = ctx.store.tail_jsonl("orders.jsonl", 10)
        if not items:
            await message.answer("Nessun ordine registrato.")
            return
        lines = []
        for item in items:
            lines.append(
                f"- {item.get('order_id')} | @{item.get('username')} | EUR {item.get('total')} | {item.get('details')}"
            )
        await message.answer("Ultimi ordini:\n" + "\n".join(lines))

    @router.message(Command("payments"))
    async def payments(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        items = ctx.store.tail_jsonl("payments.jsonl", 10)
        if not items:
            await message.answer("Nessun pagamento registrato.")
            return
        lines = []
        for item in items:
            lines.append(
                f"- @{item.get('username')} | {item.get('details')} | {item.get('status', 'pending')}"
            )
        await message.answer("Ultimi pagamenti:\n" + "\n".join(lines))

    @router.message(Command("shipping_list"))
    async def shipping_list(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        if not ctx.shipping_rules:
            await message.answer("Nessuna regola spedizione configurata.")
            return
        await message.answer(
            "Regole spedizione:\n" + "\n".join(f"- {k}: EUR {v}" for k, v in ctx.shipping_rules.items())
        )

    @router.message(Command("shipping_set"))
    async def shipping_set(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        parts = (message.text or "").split()
        if len(parts) < 3:
            await message.answer("Uso: /shipping_set <PAESE> <costo>")
            return
        try:
            cost = float(parts[2])
        except ValueError:
            await message.answer("Costo non valido.")
            return
        ctx.shipping_rules[parts[1].upper()] = cost
        ctx.save_shipping()
        await message.answer("Regola spedizione salvata.")

    @router.message(Command("company_view"))
    async def company_view(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        await message.answer(format_company(ctx.company))

    @router.message(Command("company_set"))
    async def company_set(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        raw = (message.text or "").replace("/company_set", "").strip()
        parts = [p.strip() for p in raw.split("|", 1)]
        if len(parts) < 2:
            await message.answer("Uso: /company_set <campo>|<valore>")
            return
        ctx.company[parts[0]] = parts[1]
        ctx.save_company()
        await message.answer("Info azienda aggiornata.")

    @router.message(Command("payment_add"))
    async def payment_add(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        method = (message.text or "").replace("/payment_add", "").strip()
        if not method:
            await message.answer("Uso: /payment_add <metodo>")
            return
        if method not in ctx.payment_methods:
            ctx.payment_methods.append(method)
            ctx.save_payment_methods()
        await message.answer("Metodo di pagamento aggiunto.")

    @router.message(Command("payment_del"))
    async def payment_del(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        method = (message.text or "").replace("/payment_del", "").strip()
        ctx.payment_methods = [m for m in ctx.payment_methods if m != method]
        ctx.save_payment_methods()
        await message.answer("Metodo di pagamento rimosso.")

    @router.message(Command("payment_list"))
    async def payment_list(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        await message.answer(format_payments(ctx.payment_methods, ctx.settings))

    @router.message(Command("product_add"))
    async def product_add(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        raw = (message.text or "").replace("/product_add", "").strip()
        parts = [p.strip() for p in raw.split("|", 3)]
        if len(parts) < 4:
            await message.answer("Uso: /product_add <nome>|<prezzo>|<categoria>|<descrizione>")
            return
        ctx.custom_products.append(
            Product(name=parts[0], price=parts[1], category=parts[2], description=parts[3])
        )
        save_products_json(ctx.store.json_path("custom_products.json"), ctx.custom_products)
        ctx.reload_products(load_products_from_csv(ctx.settings.products_csv) + ctx.custom_products)
        await message.answer("Prodotto aggiunto e salvato.")

    @router.message(Command("product_del"))
    async def product_del(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        name = (message.text or "").replace("/product_del", "").strip()
        ctx.custom_products = [p for p in ctx.custom_products if p.name.lower() != name.lower()]
        save_products_json(ctx.store.json_path("custom_products.json"), ctx.custom_products)
        ctx.reload_products(load_products_from_csv(ctx.settings.products_csv) + ctx.custom_products)
        await message.answer("Prodotto rimosso se presente.")

    @router.message(Command("faq_add"))
    async def faq_add(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        raw = (message.text or "").replace("/faq_add", "").strip()
        parts = [p.strip() for p in raw.split("|", 1)]
        if len(parts) < 2:
            await message.answer("Uso: /faq_add <keyword>|<risposta>")
            return
        ctx.faq[parts[0].lower()] = parts[1]
        ctx.save_faq()
        await message.answer("FAQ aggiunta.")

    @router.message(Command("faq_del"))
    async def faq_del(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        key = (message.text or "").replace("/faq_del", "").strip().lower()
        ctx.faq.pop(key, None)
        ctx.save_faq()
        await message.answer("FAQ rimossa.")

    @router.message(Command("faq_list"))
    async def faq_list(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        await message.answer("FAQ:\n" + "\n".join(f"- {k}" for k in sorted(ctx.faq.keys())))

    @router.message(Command("crypto_set"))
    async def crypto_set(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        raw = (message.text or "").replace("/crypto_set", "").strip()
        parts = [p.strip() for p in raw.split("|", 1)]
        if len(parts) < 2:
            await message.answer("Uso: /crypto_set <network>|<address>")
            return
        ctx.crypto[parts[0].lower()] = parts[1]
        ctx.save_crypto()
        await message.answer("Indirizzo crypto salvato.")

    @router.message(Command("crypto_list"))
    async def crypto_list(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        await message.answer("Indirizzi crypto:\n" + "\n".join(f"- {k}: {v}" for k, v in ctx.crypto.items()))

    @router.message(Command("promo_set"))
    async def promo_set(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        raw = (message.text or "").replace("/promo_set", "").strip()
        parts = [p.strip() for p in raw.split("|", 1)]
        if len(parts) < 2:
            await message.answer("Uso: /promo_set <stagione>|<testo>")
            return
        ctx.seasonal_promos[parts[0].lower()] = parts[1]
        ctx.save_seasonal_promos()
        await message.answer("Promo stagionale salvata.")

    @router.message(Command("checkout"))
    async def checkout(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 2:
            await message.answer("Uso: /checkout <importo> [descrizione]")
            return
        try:
            amount = float(parts[1])
        except ValueError:
            await message.answer("Importo non valido.")
            return
        description = parts[2] if len(parts) >= 3 else "Oro Naturale order"
        from ..services import create_stripe_link

        link = create_stripe_link(amount, ctx.settings, description)
        if not link:
            await message.answer("Stripe non configurato. Imposta STRIPE_SECRET_KEY.")
            return
        await message.answer(f"Link Stripe: {link}")

    @router.message(Command("tracking_add"))
    async def tracking_add(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        raw = (message.text or "").replace("/tracking_add", "").strip()
        parts = [p.strip() for p in raw.split("|", 4)]
        if len(parts) < 5:
            await message.answer("Uso: /tracking_add <order_id>|<carrier>|<code>|<status>|<url>")
            return
        shipments = ctx.store.load_json("shipments.json", {})
        shipments[parts[0]] = {
            "carrier": parts[1],
            "code": parts[2],
            "status": parts[3],
            "url": parts[4],
        }
        ctx.store.save_json("shipments.json", shipments)
        await message.answer("Tracking salvato.")
        for user_id, record in ctx.customers.items():
            for order in record.get("orders", []):
                if order.get("order_id") == parts[0] and record.get("chat_id"):
                    try:
                        await message.bot.send_message(
                            int(record["chat_id"]),
                            f"Il tuo ordine {parts[0]} è stato spedito.\n"
                            f"Corriere: {parts[1]}\n"
                            f"Codice: {parts[2]}\n"
                            f"Stato: {parts[3]}\n"
                            f"Link: {parts[4]}",
                        )
                    except Exception:
                        pass

    @router.message(Command("tracking_del"))
    async def tracking_del(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        order_id = (message.text or "").replace("/tracking_del", "").strip()
        if not order_id:
            await message.answer("Uso: /tracking_del <order_id>")
            return
        shipments = ctx.store.load_json("shipments.json", {})
        shipments.pop(order_id, None)
        ctx.store.save_json("shipments.json", shipments)
        await message.answer("Tracking rimosso.")

    @router.message(Command("reload"))
    async def reload_products(message: Message) -> None:
        if not admin_only(message):
            await message.answer("Comando riservato agli admin.")
            return
        ctx.reload_products(load_products_from_csv(ctx.settings.products_csv))
        await message.answer("Catalogo ricaricato.")

    return router
