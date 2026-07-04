# oro_naturale/routers/admin.py
from __future__ import annotations

import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ..context import BotContext
from ..keyboards import (
    admin_dashboard_menu,
    admin_order_actions_menu,
    admin_orders_menu,
    format_admin_dashboard,
)
from ..models import Product
from ..services import format_company, format_payments, is_admin_user
from ..storage import load_products_from_db, save_products_json


def build_admin_router(ctx: BotContext) -> Router:
    router = Router()

    # ─────────────────────────────────────────────────────────────
    #  Guard helper
    # ─────────────────────────────────────────────────────────────

    def is_admin(user_id: int | None) -> bool:
        return is_admin_user(user_id, ctx.settings)

    async def _deny_message(message: Message) -> None:
        await message.answer("Comando riservato agli admin.")

    async def _deny_callback(callback: CallbackQuery) -> None:
        await callback.answer("⛔ Non autorizzato.", show_alert=True)

    # ─────────────────────────────────────────────────────────────
    #  Helpers ordini
    # ─────────────────────────────────────────────────────────────

    def _all_orders() -> list[dict]:
        """Raccoglie tutti gli ordini da tutti i clienti."""
        orders = []
        for uid, record in ctx.customers.items():
            for order in record.get("orders", []):
                orders.append({
                    "id":            order.get("order_id", ""),
                    "customer_name": record.get("name", uid),
                    "total":         order.get("total", 0.0),
                    "status":        order.get("status", "pending"),
                    "date":          _ts_to_date(order.get("ts", 0)),
                    "user_id":       uid,
                })
        return sorted(orders, key=lambda o: o.get("date", ""), reverse=True)

    def _find_order(order_id: str) -> tuple[dict | None, str | None]:
        """Restituisce (order_dict, user_id) oppure (None, None)."""
        for uid, record in ctx.customers.items():
            for order in record.get("orders", []):
                if order.get("order_id") == order_id:
                    return order, uid
        return None, None

    def _ts_to_date(ts: int) -> str:
        if not ts:
            return "—"
        import datetime
        return datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")

    # ─────────────────────────────────────────────────────────────
    #  /admin — pannello testuale + inline dashboard
    # ─────────────────────────────────────────────────────────────

    @router.message(Command("admin"))
    async def admin_help(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return

        pending = ctx.pending_orders_count()
        text    = format_admin_dashboard(
            pending_count    = pending,
            today_revenue    = 0.0,        # TODO: calcolo da payments.jsonl
            active_products  = ctx.active_products_count(),
            total_customers  = ctx.total_customers_count(),
            month_revenue    = 0.0,        # TODO: calcolo da payments.jsonl
            avg_rating       = ctx.avg_rating(),
        )
        await message.answer(
            text,
            reply_markup=admin_dashboard_menu(pending),
            parse_mode="HTML",
        )

    # ─────────────────────────────────────────────────────────────
    #  CALLBACK — Dashboard inline
    # ─────────────────────────────────────────────────────────────

    @router.callback_query(F.data == "admin_dashboard")
    async def cb_admin_dashboard(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return

        pending = ctx.pending_orders_count()
        text    = format_admin_dashboard(
            pending_count    = pending,
            today_revenue    = 0.0,
            active_products  = ctx.active_products_count(),
            total_customers  = ctx.total_customers_count(),
            month_revenue    = 0.0,
            avg_rating       = ctx.avg_rating(),
        )
        await callback.message.edit_text(
            text,
            reply_markup=admin_dashboard_menu(pending),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data == "admin_orders")
    async def cb_admin_orders(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return

        orders = _all_orders()
        if not orders:
            await callback.answer("Nessun ordine presente.", show_alert=True)
            return

        await callback.message.edit_text(
            f"📦 <b>Ordini</b> — {len(orders)} totali",
            reply_markup=admin_orders_menu(orders),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("admin_order:"))
    async def cb_admin_order_detail(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return

        order_id = callback.data.split(":", 1)[1]
        order, user_uid = _find_order(order_id)
        if not order:
            await callback.answer("Ordine non trovato.", show_alert=True)
            return

        record = ctx.customers.get(str(user_uid), {})
        text = (
            f"🔍 <b>Ordine #{order_id}</b>\n\n"
            f"👤 Cliente: {record.get('name', user_uid)}\n"
            f"💴 Totale: € {float(order.get('total', 0)):.2f}\n"
            f"📅 Data: {_ts_to_date(order.get('ts', 0))}\n"
            f"🚚 Stato: {order.get('status', 'pending')}\n"
            f"📍 Indirizzo: {record.get('address', '—')}"
        )
        await callback.message.edit_text(
            text,
            reply_markup=admin_order_actions_menu(order_id),
            parse_mode="HTML",
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("admin_ship:"))
    async def cb_admin_ship(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return

        order_id   = callback.data.split(":", 1)[1]
        order, user_uid = _find_order(order_id)
        if not order:
            await callback.answer("Ordine non trovato.", show_alert=True)
            return

        order["status"] = "shipped"
        ctx.save_customers()

        # Notifica all'utente
        record = ctx.customers.get(str(user_uid), {})
        chat_id = record.get("chat_id")
        if chat_id:
            try:
                await callback.bot.send_message(
                    int(chat_id),
                    f"🚚 Il tuo ordine <code>#{order_id}</code> è stato spedito!\n"
                    "Usa /tracking per seguire la spedizione.",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        await callback.answer("✅ Ordine segnato come SPEDITO", show_alert=True)
        await callback.message.edit_reply_markup(
            reply_markup=admin_order_actions_menu(order_id)
        )

    @router.callback_query(F.data.startswith("admin_cancel:"))
    async def cb_admin_cancel(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return

        order_id        = callback.data.split(":", 1)[1]
        order, user_uid = _find_order(order_id)
        if not order:
            await callback.answer("Ordine non trovato.", show_alert=True)
            return

        order["status"] = "cancelled"
        ctx.save_customers()

        record  = ctx.customers.get(str(user_uid), {})
        chat_id = record.get("chat_id")
        if chat_id:
            try:
                await callback.bot.send_message(
                    int(chat_id),
                    f"❌ Il tuo ordine <code>#{order_id}</code> è stato annullato.\n"
                    "Contatta il supporto per maggiori informazioni.",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        await callback.answer("Ordine annullato.", show_alert=True)
        await callback.message.edit_reply_markup(
            reply_markup=admin_order_actions_menu(order_id)
        )

    @router.callback_query(F.data.startswith("admin_contact:"))
    async def cb_admin_contact(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return

        order_id        = callback.data.split(":", 1)[1]
        _, user_uid     = _find_order(order_id)
        if not user_uid:
            await callback.answer("Ordine non trovato.", show_alert=True)
            return

        record  = ctx.customers.get(str(user_uid), {})
        chat_id = record.get("chat_id")
        if chat_id:
            await callback.answer(
                f"Chat ID utente: {chat_id}\nUsa /sendmessage per contattarlo.",
                show_alert=True,
            )
        else:
            await callback.answer("Chat ID non disponibile.", show_alert=True)

    # ── Stub: admin_product_new / admin_catalog / admin_stats / admin_settings ──
    # Questi sono placeholder — implementa le schermate di gestione catalogo
    # in un router separato (es. routers/admin_catalog.py) quando pronto.

    @router.callback_query(F.data == "admin_product_new")
    async def cb_admin_product_new(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return
        await callback.answer(
            "Usa il comando /product_add per aggiungere prodotti.", show_alert=True
        )

    @router.callback_query(F.data == "admin_catalog")
    async def cb_admin_catalog(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return
        await callback.answer(
            f"Catalogo: {len(ctx.products)} prodotti attivi.", show_alert=True
        )

    @router.callback_query(F.data == "admin_stats")
    async def cb_admin_stats(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return
        orders = _all_orders()
        total_revenue = sum(float(o.get("total", 0)) for o in orders)
        await callback.answer(
            f"Ordini totali: {len(orders)}\n"
            f"Fatturato totale: € {total_revenue:.2f}\n"
            f"Clienti: {ctx.total_customers_count()}\n"
            f"Rating medio: {ctx.avg_rating():.1f}/5",
            show_alert=True,
        )

    @router.callback_query(F.data == "admin_settings")
    async def cb_admin_settings(callback: CallbackQuery) -> None:
        uid = callback.from_user.id if callback.from_user else None
        if not is_admin(uid):
            await _deny_callback(callback)
            return
        await callback.answer(
            "Impostazioni disponibili via comandi /shipping_set, /company_set, ecc.",
            show_alert=True,
        )

    # ─────────────────────────────────────────────────────────────
    #  Comandi testo (invariati + migliorati)
    # ─────────────────────────────────────────────────────────────

    @router.message(Command("orders"))
    async def orders(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        items = ctx.store.tail_jsonl("orders.jsonl", 10)
        if not items:
            await message.answer("Nessun ordine registrato.")
            return
        lines = [
            f"- {i.get('order_id')} | @{i.get('username')} | "
            f"EUR {i.get('total')} | {i.get('details')}"
            for i in items
        ]
        await message.answer("Ultimi ordini:\n" + "\n".join(lines))

    @router.message(Command("payments"))
    async def payments(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        items = ctx.store.tail_jsonl("payments.jsonl", 10)
        if not items:
            await message.answer("Nessun pagamento registrato.")
            return
        lines = [
            f"- @{i.get('username')} | {i.get('details')} | {i.get('status', 'pending')}"
            for i in items
        ]
        await message.answer("Ultimi pagamenti:\n" + "\n".join(lines))

    @router.message(Command("shipping_list"))
    async def shipping_list(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        if not ctx.shipping_rules:
            await message.answer("Nessuna regola spedizione configurata.")
            return
        await message.answer(
            "Regole spedizione:\n"
            + "\n".join(f"- {k}: EUR {v}" for k, v in ctx.shipping_rules.items())
        )

    @router.message(Command("shipping_set"))
    async def shipping_set(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
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
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        await message.answer(format_company(ctx.company))

    @router.message(Command("company_set"))
    async def company_set(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
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
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
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
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        method = (message.text or "").replace("/payment_del", "").strip()
        ctx.payment_methods = [m for m in ctx.payment_methods if m != method]
        ctx.save_payment_methods()
        await message.answer("Metodo di pagamento rimosso.")

    @router.message(Command("payment_list"))
    async def payment_list(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        await message.answer(format_payments(ctx.payment_methods, ctx.settings))

    @router.message(Command("product_add"))
    async def product_add(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        raw   = (message.text or "").replace("/product_add", "").strip()
        parts = [p.strip() for p in raw.split("|", 4)]
        if len(parts) < 4:
            await message.answer("Uso: /product_add <nome>|<prezzo>|<categoria>|<descrizione>|[image_url]")
            return
        try:
            price = float(parts[1].replace(",", "."))
        except ValueError:
            await message.answer("Prezzo non valido. Usa un numero, es. 12.95")
            return
        image_url = parts[4] if len(parts) > 4 else ""
        ctx.custom_products.append(
            Product(
                id=f"custom-{int(time.time())}",
                name=parts[0],
                price=price,
                category=parts[2],
                description=parts[3],
                image_url=image_url,
            )
        )
        save_products_json(ctx.store.json_path("custom_products.json"), ctx.custom_products)
        ctx.reload_products(load_products_from_db() + ctx.custom_products)
        await message.answer(f"Prodotto aggiunto. Totale prodotti: {len(ctx.products)}")

    @router.message(Command("product_del"))
    async def product_del(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        name = (message.text or "").replace("/product_del", "").strip()
        ctx.custom_products = [p for p in ctx.custom_products if p.name.lower() != name.lower()]
        save_products_json(ctx.store.json_path("custom_products.json"), ctx.custom_products)
        ctx.reload_products(load_products_from_db() + ctx.custom_products)
        await message.answer("Prodotto rimosso se presente.")

    @router.message(Command("faq_add"))
    async def faq_add(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        raw   = (message.text or "").replace("/faq_add", "").strip()
        parts = [p.strip() for p in raw.split("|", 1)]
        if len(parts) < 2:
            await message.answer("Uso: /faq_add <keyword>|<risposta>")
            return
        ctx.faq[parts[0].lower()] = parts[1]
        ctx.save_faq()
        await message.answer("FAQ aggiunta.")

    @router.message(Command("faq_del"))
    async def faq_del(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        key = (message.text or "").replace("/faq_del", "").strip().lower()
        ctx.faq.pop(key, None)
        ctx.save_faq()
        await message.answer("FAQ rimossa.")

    @router.message(Command("faq_list"))
    async def faq_list(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        if not ctx.faq:
            await message.answer("Nessuna FAQ configurata.")
            return
        await message.answer("FAQ:\n" + "\n".join(f"- {k}" for k in sorted(ctx.faq.keys())))

    @router.message(Command("promo_set"))
    async def promo_set(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        raw   = (message.text or "").replace("/promo_set", "").strip()
        parts = [p.strip() for p in raw.split("|", 1)]
        if len(parts) < 2:
            await message.answer("Uso: /promo_set <stagione>|<testo>")
            return
        ctx.seasonal_promos[parts[0].lower()] = parts[1]
        ctx.save_seasonal_promos()
        await message.answer("Promo stagionale salvata.")

    @router.message(Command("checkout"))
    async def checkout(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
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
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        raw   = (message.text or "").replace("/tracking_add", "").strip()
        parts = [p.strip() for p in raw.split("|", 4)]
        if len(parts) < 5:
            await message.answer("Uso: /tracking_add <order_id>|<carrier>|<code>|<status>|<url>")
            return
        shipments           = ctx.store.load_json("shipments.json", {})
        shipments[parts[0]] = {
            "carrier": parts[1],
            "code":    parts[2],
            "status":  parts[3],
            "url":     parts[4],
        }
        ctx.store.save_json("shipments.json", shipments)
        await message.answer("Tracking salvato.")

        for user_uid, record in ctx.customers.items():
            for order in record.get("orders", []):
                if order.get("order_id") == parts[0] and record.get("chat_id"):
                    try:
                        await message.bot.send_message(
                            int(record["chat_id"]),
                            f"📦 Il tuo ordine <code>{parts[0]}</code> è stato spedito!\n"
                            f"Corriere: {parts[1]}\n"
                            f"Codice: {parts[2]}\n"
                            f"Stato: {parts[3]}\n"
                            f"🔗 {parts[4]}",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

    @router.message(Command("tracking_del"))
    async def tracking_del(message: Message) -> None:
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
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
        uid = message.from_user.id if message.from_user else None
        if not is_admin(uid):
            await _deny_message(message)
            return
        ctx.reload_products(load_products_from_db() + ctx.custom_products)
        await message.answer(f"Catalogo ricaricato. Totale prodotti: {len(ctx.products)}")

    return router