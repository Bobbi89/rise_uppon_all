# oro_naturale/routers/public.py
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramNetworkError

from ..catalog import (
    category_label,
    find_products,
    format_product,
    format_products,
    product_key,
    recommendations_for,
)
from ..context import BotContext
from ..keyboards import (
    # Costanti testo bottoni reply keyboard
    BTN_CARRELLO,
    BTN_CATALOGO,
    BTN_CERCA,
    BTN_NEGOZIO,
    BTN_ORDINI,
    BTN_PREFERITI,
    BTN_PROFILO,
    BTN_SUPPORTO,
    # Formatters testo
    format_favorites_empty,
    format_favorites_header,
    format_order_confirmed,
    format_order_detail,
    format_orders_header,
    format_profile,
    format_search_empty,
    format_search_header,
    format_store_info,
    format_support_info,
    format_tracking_message,
    # Keyboards
    cart_menu,
    categories_menu,
    favorites_empty_menu,
    favorites_menu,
    main_menu,
    order_confirmed_menu,
    order_detail_menu,
    orders_menu,
    payment_menu,
    product_card_menu,
    profile_menu,
    quantity_menu,
    search_no_results_menu,
    search_results_menu,
    shipping_menu,
    store_menu,
    support_menu,
    tracking_menu,
    welcome_menu,
)
from ..services import (
    create_stripe_link,
    detect_b2b,
    detect_format,
    detect_language,
    detect_preference,
    format_company,
    format_payments,
    natural_business_reply,
    process_order_payload,
    recommend_upsell,
)


async def safe_send_message(
    message_or_callback: Message | CallbackQuery,
    text: str,
    parse_mode: str = "HTML",
    reply_markup=None,
    max_retries: int = 3,
    base_delay: float = 1.0,
):
    """
    Invia un messaggio Telegram con retry automatico in caso di TelegramNetworkError.
    """
    for attempt in range(max_retries):
        try:
            if isinstance(message_or_callback, Message):
                return await message_or_callback.answer(
                    text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
            else:  # CallbackQuery
                return await message_or_callback.message.answer(
                    text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
        except TelegramNetworkError:
            if attempt == max_retries - 1:
                raise  # ultimo tentativo, rilancio
            wait = base_delay * (2 ** attempt)
            print(f"[safe_send_message] TelegramNetworkError, ritento tra {wait}s...")
            await asyncio.sleep(wait)
    return None


def build_public_router(ctx: BotContext) -> Router:
    router = Router()

    # ─────────────────────────────────────────────────────────────
    #  Helper utente / carrello
    # ─────────────────────────────────────────────────────────────

    def customer_record(user_id: int) -> dict[str, Any]:
        record = ctx.customers.get(str(user_id), {})
        record.setdefault("stage", "idle")
        record.setdefault("cart", {})
        return record

    def save_customer(user_id: int, record: dict) -> None:
        ctx.customers[str(user_id)] = record
        ctx.save_customers()

    def get_product_by_key(key: str):
        for product in ctx.products:
            if product_key(product) == key:
                return product
        return None

    def get_cart(user_id: int) -> dict[str, int]:
        return dict(customer_record(user_id).get("cart", {}))

    def set_cart(user_id: int, cart: dict[str, int]) -> None:
        record = customer_record(user_id)
        record["cart"] = cart
        save_customer(user_id, record)

    def add_to_cart(user_id: int, product_key_str: str, qty: int) -> None:
        cart = get_cart(user_id)
        cart[product_key_str] = cart.get(product_key_str, 0) + max(1, qty)
        set_cart(user_id, cart)

    def remove_from_cart(user_id: int, product_key_str: str) -> None:
        cart = get_cart(user_id)
        cart.pop(product_key_str, None)
        set_cart(user_id, cart)

    def clear_cart(user_id: int) -> None:
        set_cart(user_id, {})

    def cart_count(user_id: int) -> int:
        return sum(get_cart(user_id).values())

    def cart_text_summary(user_id: int) -> str:
        cart = get_cart(user_id)
        if not cart:
            return "Il tuo carrello è vuoto."
        lines = ["🛒 <b>Carrello:</b>"]
        for key, qty in cart.items():
            product = get_product_by_key(key)
            if product and product.price:
                price = float(str(product.price).replace(",", "."))
                lines.append(f"• {product.name} x{qty} = € {price * qty:.2f}")
            else:
                lines.append(f"• {key} x{qty}")
        return "\n".join(lines)

    def build_orders_list(user_id: int) -> list[dict]:
        """Costruisce la lista ordini nel formato richiesto da orders_menu()."""
        record = customer_record(user_id)
        result = []
        for o in record.get("orders", []):
            result.append({
                "id":     o.get("order_id", ""),
                "date":   _ts_to_date(o.get("ts", 0)),
                "total":  o.get("total", 0.0),
                "status": o.get("status", "pending"),
            })
        return result

    def _ts_to_date(ts: int) -> str:
        if not ts:
            return "—"
        import datetime
        return datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")

    # ─────────────────────────────────────────────────────────────
    #  SCREEN 01 — /start  /help
    # ─────────────────────────────────────────────────────────────

    @router.message(Command("start"))
    async def start(message: Message) -> None:
        user_id = message.from_user.id if message.from_user else None
        if user_id:
            record = customer_record(user_id)
            record["chat_id"] = message.chat.id
            record.setdefault("stage", "qualify")
            save_customer(user_id, record)
            count = cart_count(user_id)
        else:
            count = 0

        await safe_send_message(
            message,
            "🌿 <b>Benvenuto in Oro Naturale</b>\n\n"
            "Oli EVO, vini, cosmetici e confezioni regalo dall'Umbria.\n\n"
            "Usa il menu qui sotto per navigare il catalogo, "
            "gestire il carrello e completare i tuoi ordini.",
            reply_markup=main_menu(count, ctx.settings.webapp_url),
        )
        await safe_send_message(
            message,
            "Cosa vuoi fare oggi?",
            reply_markup=welcome_menu(ctx.settings.webapp_url),
        )

    @router.message(Command("help"))
    async def help_cmd(message: Message) -> None:
        await start(message)

    # ── callback dal welcome_menu ──────────────────────────────────

    @router.callback_query(F.data == "main_menu")
    async def cb_main_menu(callback: CallbackQuery) -> None:
        user_id = callback.from_user.id if callback.from_user else 0
        count   = cart_count(user_id)
        await safe_send_message(
            callback,
            "🏠 Menu principale",
            reply_markup=main_menu(count, ctx.settings.webapp_url),
        )
        await callback.answer()

    # ─────────────────────────────────────────────────────────────
    #  SCREEN 02 — CATALOGO
    #  Reply keyboard: 🛍️ Catalogo
    #  Callback: show_categories, cat:*, cat_page:*, prod:*, back_cat:*
    # ─────────────────────────────────────────────────────────────

    @router.message(F.text == BTN_CATALOGO)
    @router.message(Command("catalogo"))
    async def catalog(message: Message) -> None:
        await safe_send_message(
            message,
            "🛍️ <b>Catalogo Oro Naturale</b>\n\nScegli una categoria:",
            reply_markup=categories_menu(),
        )

    @router.callback_query(F.data == "show_categories")
    async def cb_show_categories(callback: CallbackQuery) -> None:
        await safe_send_message(
            callback,
            "🛍️ <b>Catalogo Oro Naturale</b>\n\nScegli una categoria:",
            reply_markup=categories_menu(),
        )
        await callback.answer()

    async def send_category(callback: CallbackQuery, category_name: str, page: int = 0) -> None:
        """Invia i prodotti di una categoria (10 per pagina)."""
        if category_name == "featured":
            products = [p for p in ctx.products if getattr(p, "featured", False)]
        else:
            products = [p for p in ctx.products if p.category == category_name]

        if not products:
            await callback.answer("Nessun prodotto in questa categoria.", show_alert=True)
            return

        page_items = products[page * 10 : (page + 1) * 10]
        if not page_items:
            page, page_items = 0, products[:10]

        await safe_send_message(
            callback,
            f"<b>{category_label(category_name)}</b> — {len(products)} prodotti",
        )
        for product in page_items:
            key     = product_key(product)
            caption = format_product(product)
            stock   = int(getattr(product, "stock", 99))
            user_id = callback.from_user.id if callback.from_user else 0
            is_fav  = ctx.is_favorite(user_id, key)

            kb = product_card_menu(key, category_name, stock, is_fav)

            sent = False
            if product.image_url:
                try:
                    await callback.message.answer_photo(
                        photo=product.image_url,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=kb,
                    )
                    sent = True
                except Exception:
                    # URL immagine non valido/scaduto: fallback su testo
                    sent = False
            if not sent:
                await safe_send_message(
                    callback,
                    caption,
                    reply_markup=kb,
                )
        await callback.answer()

    @router.callback_query(F.data.startswith("cat:"))
    async def cb_category(callback: CallbackQuery) -> None:
        await send_category(callback, callback.data.split(":", 1)[1])

    @router.callback_query(F.data.startswith("cat_page:"))
    async def cb_cat_page(callback: CallbackQuery) -> None:
        # cat_page:<category>:<page>
        parts = callback.data.split(":", 2)
        page  = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        await send_category(callback, parts[1], page)

    @router.callback_query(F.data.startswith("back_cat:"))
    async def cb_back_cat(callback: CallbackQuery) -> None:
        await send_category(callback, callback.data.split(":", 1)[1])

    @router.callback_query(F.data.startswith("prod:"))
    async def cb_product(callback: CallbackQuery) -> None:
        """Mostra scheda prodotto da product_key."""
        pid     = callback.data.split(":", 1)[1]
        product = get_product_by_key(pid)
        if not product:
            await callback.answer("Prodotto non trovato.", show_alert=True)
            return
        user_id = callback.from_user.id if callback.from_user else 0
        is_fav  = ctx.is_favorite(user_id, pid)
        stock   = int(getattr(product, "stock", 99))
        caption = format_product(product)
        kb      = product_card_menu(pid, product.category or "", stock, is_fav)

        sent = False
        if product.image_url:
            try:
                await callback.message.answer_photo(
                    photo=product.image_url,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
                sent = True
            except Exception:
                sent = False
        if not sent:
            await safe_send_message(
                callback,
                caption,
                reply_markup=kb,
            )
        await callback.answer()

    @router.callback_query(F.data.startswith("info:"))
    async def cb_info(callback: CallbackQuery) -> None:
        """Dettagli aggiuntivi prodotto (stessa scheda per ora)."""
        pid     = callback.data.split(":", 1)[1]
        product = get_product_by_key(pid)
        if not product:
            await callback.answer("Prodotto non trovato.", show_alert=True)
            return
        details = getattr(product, "details", {}) or {}
        lines   = [f"📋 <b>Dettagli — {product.name}</b>\n"]
        if isinstance(details, dict):
            for k, v in details.items():
                lines.append(f"• <b>{k}</b>: {v}")
        if len(lines) == 1:
            lines.append("Nessun dettaglio aggiuntivo disponibile.")
        await safe_send_message(
            callback,
            "\n".join(lines),
        )
        await callback.answer()

    # ─────────────────────────────────────────────────────────────
    #  QUANTITÀ — qty:* e add:*
    # ─────────────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("qty:"))
    async def cb_quantity(callback: CallbackQuery) -> None:
        _, product_id, qty_raw = callback.data.split(":", 2)
        qty = max(0, int(qty_raw))
        if qty == 0:
            # Rimuovi dal carrello se l'utente preme 🗑️ con qty=0
            if callback.from_user:
                remove_from_cart(callback.from_user.id, product_id)
            await callback.answer("Prodotto rimosso dal carrello.")
            return
        await callback.message.edit_reply_markup(
            reply_markup=quantity_menu(product_id, qty)
        )
        await callback.answer(f"Quantità: {qty}")

    @router.callback_query(F.data.startswith("add:"))
    async def cb_add(callback: CallbackQuery) -> None:
        parts      = callback.data.split(":")
        product_id = parts[1]
        qty        = max(1, int(parts[2])) if len(parts) > 2 else 1

        if not callback.from_user:
            await callback.answer("Utente non trovato.")
            return

        product = get_product_by_key(product_id)
        if not product:
            await callback.answer("Prodotto non trovato.", show_alert=True)
            return

        add_to_cart(callback.from_user.id, product_id, qty)
        count = cart_count(callback.from_user.id)

        # Aggiorna reply keyboard con contatore carrello
        await safe_send_message(
            callback,
            f"✅ <b>{product.name}</b> aggiunto al carrello (x{qty})\n"
            f"🛒 Totale articoli: {count}",
            reply_markup=main_menu(count, ctx.settings.webapp_url),
        )
        await callback.answer(f"Aggiunto x{qty}!")

    @router.callback_query(F.data == "noop")
    async def cb_noop(callback: CallbackQuery) -> None:
        await callback.answer()

    # ─────────────────────────────────────────────────────────────
    #  MINI APP — ordini inviati dalla webapp via sendData
    # ─────────────────────────────────────────────────────────────

    @router.message(F.web_app_data)
    async def webapp_order(message: Message) -> None:
        """Riceve l'ordine dalla Mini App (Telegram.WebApp.sendData)."""
        try:
            payload = json.loads(message.web_app_data.data)
        except (json.JSONDecodeError, AttributeError):
            await safe_send_message(message, "⚠️ Dati ordine non validi. Riprova dalla Mini App.")
            return
        if payload.get("type") != "order":
            return

        user_id = message.from_user.id if message.from_user else 0
        order_id = payload.get("order_id") or f"ON{int(time.time())}"
        total = float(payload.get("total") or 0)
        customer = payload.get("customer") or {}
        items = payload.get("items") or []
        method = payload.get("payment_method") or "da definire"

        ctx.store.append_jsonl("orders.jsonl", {
            "order_id": order_id,
            "ts": int(time.time()),
            "user_id": user_id,
            "username": message.from_user.username if message.from_user else None,
            "chat_id": message.chat.id,
            "total": total,
            "shipping": payload.get("shipping"),
            "payment_method": method,
            "customer": customer,
            "items": items,
            "source": "miniapp",
        })

        record = customer_record(user_id)
        record["chat_id"] = message.chat.id
        record["stage"] = "payment_pending"
        save_customer(user_id, record)

        item_lines = "\n".join(
            f"  • {i.get('quantity', 1)}× {i.get('name', '?')} — € {float(i.get('price', 0)) * int(i.get('quantity', 1)):.2f}"
            for i in items
        )
        await safe_send_message(
            message,
            f"🌿 <b>Ordine ricevuto!</b> <code>#{order_id}</code>\n\n"
            f"{item_lines}\n\n"
            f"💰 Totale: <b>€ {total:.2f}</b>\n"
            f"💳 Pagamento: {method}\n"
            f"📦 Spedizione a: {customer.get('address', '')}, {customer.get('city', '')}\n\n"
            "Ti invieremo a breve la conferma e le istruzioni di pagamento. Grazie! 🙏",
            reply_markup=main_menu(cart_count(user_id), ctx.settings.webapp_url),
        )

        for admin_id in ctx.settings.admin_chat_ids:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"🔔 <b>NUOVO ORDINE MINI APP</b> <code>#{order_id}</code>\n"
                    f"👤 @{message.from_user.username or user_id}\n"
                    f"🙍 {customer.get('name', '?')} · {customer.get('phone', '?')}\n"
                    f"📍 {customer.get('address', '')}, {customer.get('zip', '')} {customer.get('city', '')}\n"
                    f"💴 € {total:.2f} | {method}\n"
                    f"{item_lines}",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────
    #  SCREEN 03 — CARRELLO
    #  Reply keyboard: 🛒 Carrello  /  callback: show_cart, cart_clear,
    #  cart_edit, cart_coupon, checkout_start, ship:*, pay:*, rem:*
    # ─────────────────────────────────────────────────────────────

    @router.message(F.text.startswith(BTN_CARRELLO))   # gestisce anche "🛒 Carrello (N)"
    @router.message(Command("carrello"))
    async def cart(message: Message) -> None:
        if not message.from_user:
            return
        user_id  = message.from_user.id
        cart_map = get_cart(user_id)
        has      = bool(cart_map)

        await safe_send_message(
            message,
            cart_text_summary(user_id),
            reply_markup=cart_menu(has),
        )

    @router.callback_query(F.data == "show_cart")
    async def cb_show_cart(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        user_id  = callback.from_user.id
        cart_map = get_cart(user_id)
        has      = bool(cart_map)

        await safe_send_message(
            callback,
            cart_text_summary(user_id),
            reply_markup=cart_menu(has),
        )
        await callback.answer()

    @router.callback_query(F.data == "cart_clear")
    async def cb_cart_clear(callback: CallbackQuery) -> None:
        if callback.from_user:
            clear_cart(callback.from_user.id)
        await callback.answer("Carrello svuotato.")
        await callback.message.edit_text(
            "🛒 Carrello svuotato.\nUsa il catalogo per aggiungere prodotti.",
            reply_markup=cart_menu(False),
        )

    @router.callback_query(F.data == "cart_edit")
    async def cb_cart_edit(callback: CallbackQuery) -> None:
        """Mostra i prodotti nel carrello con selettori quantità."""
        if not callback.from_user:
            return
        user_id  = callback.from_user.id
        cart_map = get_cart(user_id)
        if not cart_map:
            await callback.answer("Carrello vuoto.", show_alert=True)
            return
        await callback.answer()
        for key, qty in cart_map.items():
            product = get_product_by_key(key)
            name    = product.name if product else key
            await safe_send_message(
                callback,
                f"✏️ <b>{name}</b>",
                reply_markup=quantity_menu(key, qty),
            )

    @router.callback_query(F.data == "cart_coupon")
    async def cb_cart_coupon(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        record = customer_record(callback.from_user.id)
        record["stage"] = "coupon_collect"
        save_customer(callback.from_user.id, record)
        await safe_send_message(
            callback,
            "🏷️ Inserisci il codice coupon:",
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("rem:"))
    async def cb_remove(callback: CallbackQuery) -> None:
        if callback.from_user:
            remove_from_cart(callback.from_user.id, callback.data.split(":", 1)[1])
        await callback.answer("Rimosso dal carrello.")
        await cb_show_cart(callback)

    # ── Checkout step 1 — Scelta spedizione ──────────────────────

    @router.callback_query(F.data == "checkout_start")
    async def cb_checkout_start(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        user_id  = callback.from_user.id
        cart_map = get_cart(user_id)
        if not cart_map:
            await callback.answer("Il carrello è vuoto.", show_alert=True)
            return
        await safe_send_message(
            callback,
            "📦 <b>Spedizione</b>\n\nScegli come vuoi ricevere il tuo ordine:",
            reply_markup=shipping_menu(float(ctx.settings.default_shipping)),
        )
        await callback.answer()

    # ── Checkout step 2 — Scelta pagamento ───────────────────────

    @router.callback_query(F.data.startswith("ship:"))
    async def cb_ship(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        user_id  = callback.from_user.id
        method   = callback.data.split(":", 1)[1]   # "home" | "pickup"

        # Calcola costo spedizione
        if method == "home":
            shipping_cost  = float(ctx.settings.default_shipping)
            shipping_label = f"Spedizione a casa (+€{shipping_cost:.2f})"
        else:
            shipping_cost  = 0.0
            shipping_label = "Ritiro in negozio (gratuito)"

        # Calcola subtotale carrello
        cart_map = get_cart(user_id)
        subtotal = 0.0
        for key, qty in cart_map.items():
            product = get_product_by_key(key)
            if product and product.price:
                subtotal += float(str(product.price).replace(",", ".")) * qty

        # Coupon dallo stato checkout
        checkout = ctx.get_checkout(user_id)
        discount = checkout.get("discount", 0.0)
        total    = max(0.0, (subtotal + shipping_cost) * (1 - discount))

        # Salva stato checkout
        ctx.set_checkout(user_id, {
            "shipping":      method,
            "shipping_cost": shipping_cost,
            "discount":      discount,
            "coupon":        checkout.get("coupon"),
            "total":         total,
        })

        await safe_send_message(
            callback,
            f"💳 <b>Pagamento</b>\n\n"
            f"🚚 {shipping_label}\n"
            f"💴 Totale: <b>€ {total:.2f}</b>\n\n"
            f"Scegli il metodo di pagamento:",
            reply_markup=payment_menu(total),
        )
        await callback.answer()

    # ── Checkout step 3 — Pagamento ──────────────────────────────

    @router.callback_query(F.data.startswith("pay:"))
    async def cb_pay(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        user_id = callback.from_user.id
        method  = callback.data.split(":", 1)[1]   # "card" | "paypal"
        checkout = ctx.get_checkout(user_id)

        if not checkout:
            await callback.answer(
                "Sessione scaduta. Riparti dal carrello.", show_alert=True
            )
            return

        total = checkout.get("total", 0.0)

        # Genera order_id
        import hashlib
        ts       = int(time.time())
        order_id = hashlib.sha1(
            f"{user_id}{ts}".encode()
        ).hexdigest()[:8].upper()

        # Salva ordine nel profilo utente
        record = customer_record(user_id)
        shipping_method = checkout.get("shipping", "home")
        record.setdefault("orders", []).append({
            "order_id": order_id,
            "total":    total,
            "status":   "pending",
            "ts":       ts,
            "shipping": shipping_method,
            "payment":  method,
        })
        record["stage"] = "payment_pending"
        record["next_followup"] = ts + int(ctx.settings.followup_hours * 3600)
        record["followup_sent"] = False
        save_customer(user_id, record)

        # Svuota carrello e stato checkout
        clear_cart(user_id)
        ctx.clear_checkout(user_id)

        # Genera link Stripe per "card"
        stripe_link = None
        if method == "card":
            stripe_link = create_stripe_link(
                total, ctx.settings, f"Oro Naturale order {order_id}"
            )

        # Label metodo e spedizione
        method_label   = "💳 Carta di credito" if method == "card" else "💸 PayPal"
        shipping_label = (
            f"Spedizione a casa (+€{checkout.get('shipping_cost', 0):.2f})"
            if shipping_method == "home"
            else "Ritiro in negozio"
        )

        # Messaggio conferma
        confirm_text = format_order_confirmed(
            order_id       = order_id,
            total          = total,
            method_label   = method_label,
            shipping_label = shipping_label,
            address        = record.get("address"),
        )
        await safe_send_message(
            callback,
            confirm_text,
            reply_markup=order_confirmed_menu(order_id),
        )

        if stripe_link:
            await safe_send_message(
                callback,
                f"🔗 <b>Paga ora:</b>\n{stripe_link}",
            )

        # Notifica admin
        ctx.store.append_jsonl("orders.jsonl", {
            "order_id": order_id,
            "user_id":  user_id,
            "username": callback.from_user.username,
            "total":    total,
            "ts":       ts,
            "details":  f"{method} | {shipping_method}",
        })
        for admin_id in ctx.settings.admin_chat_ids:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"🔔 <b>NUOVO ORDINE</b> <code>#{order_id}</code>\n"
                    f"👤 @{callback.from_user.username or user_id}\n"
                    f"💴 € {total:.2f} | {method_label}\n"
                    f"🚚 {shipping_label}",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        await callback.answer("✅ Ordine confermato!")

    # ─────────────────────────────────────────────────────────────
    #  SCREEN 04 — I MIEI ORDINI
    #  Reply keyboard: 📦 I miei ordini
    #  Callback: orders_list, order:*
    # ─────────────────────────────────────────────────────────────

    @router.message(F.text == BTN_ORDINI)
    @router.message(Command("ordini"))
    async def my_orders(message: Message) -> None:
        if not message.from_user:
            return
        user_id    = message.from_user.id
        order_list = build_orders_list(user_id)
        await safe_send_message(
            message,
            format_orders_header(len(order_list)),
            reply_markup=orders_menu(order_list) if order_list else None,
        )

    @router.callback_query(F.data == "orders_list")
    async def cb_orders_list(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        user_id    = callback.from_user.id
        order_list = build_orders_list(user_id)
        await safe_send_message(
            callback,
            format_orders_header(len(order_list)),
            reply_markup=orders_menu(order_list) if order_list else None,
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("order:"))
    async def cb_order_detail(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        order_id = callback.data.split(":", 1)[1]
        record   = customer_record(callback.from_user.id)

        order = next(
            (o for o in record.get("orders", []) if o.get("order_id") == order_id),
            None,
        )
        if not order:
            await callback.answer("Ordine non trovato.", show_alert=True)
            return

        order_dict = {
            "id":      order_id,
            "date":    _ts_to_date(order.get("ts", 0)),
            "status":  order.get("status", "pending"),
            "total":   order.get("total", 0.0),
            "items":   "",
            "address": record.get("address", ""),
        }
        await safe_send_message(
            callback,
            format_order_detail(order_dict),
            reply_markup=order_detail_menu(order_id),
        )
        await callback.answer()

    # ─────────────────────────────────────────────────────────────
    #  SCREEN 05 — POST-VENDITA
    #  Callback: track:*, review:*
    # ─────────────────────────────────────────────────────────────

    @router.callback_query(F.data.startswith("track:"))
    async def cb_track(callback: CallbackQuery) -> None:
        order_id  = callback.data.split(":", 1)[1]
        shipments = ctx.store.load_json("shipments.json", {})
        entry     = shipments.get(order_id)

        if not entry:
            await safe_send_message(
                callback,
                f"📦 <b>Tracking ordine #{order_id}</b>\n\n"
                "Nessuna informazione di spedizione disponibile ancora.\n"
                "Riceverai una notifica appena il pacco sarà spedito.",
                reply_markup=tracking_menu(order_id),
            )
        else:
            carrier_note = (
                f"🚛 {entry.get('carrier')}  ·  <code>{entry.get('code')}</code>"
            )
            text = format_tracking_message(
                order_id    = order_id,
                status      = entry.get("status", "shipped"),
                carrier_note= carrier_note,
            )
            await safe_send_message(
                callback,
                text,
                reply_markup=tracking_menu(order_id, entry.get("url")),
            )
        await callback.answer()

    @router.callback_query(F.data.startswith("review:"))
    async def cb_review(callback: CallbackQuery) -> None:
        # review:<order_id>:<rating|skip>
        parts    = callback.data.split(":")
        order_id = parts[1]
        value    = parts[2] if len(parts) > 2 else "skip"

        if value == "skip":
            await callback.answer("Nessun problema, grazie!")
            await callback.message.edit_reply_markup(reply_markup=None)
            return

        try:
            rating = int(value)
        except ValueError:
            await callback.answer()
            return

        user_id = callback.from_user.id if callback.from_user else 0
        ctx.save_review(order_id, user_id, rating)

        stars = "⭐" * rating
        await callback.message.edit_text(
            f"🙏 Grazie per la tua recensione!\n\n"
            f"Ordine #{order_id}: {stars} ({rating}/5)"
        )
        await callback.answer("Recensione salvata!")

    # ─────────────────────────────────────────────────────────────
    #  PREFERITI
    #  Reply keyboard: ❤️ Preferiti
    #  Callback: fav_list, fav:*
    # ─────────────────────────────────────────────────────────────

    @router.message(F.text == BTN_PREFERITI)
    async def my_favorites(message: Message) -> None:
        if not message.from_user:
            return
        user_id = message.from_user.id
        fav_keys = ctx.get_favorites(user_id)
        products  = [p for p in ctx.products if product_key(p) in fav_keys]

        if not products:
            await safe_send_message(
                message,
                format_favorites_empty(),
                reply_markup=favorites_empty_menu(),
            )
            return

        prod_dicts = [
            {"id": product_key(p), "name": p.name, "price": p.price or 0}
            for p in products
        ]
        await safe_send_message(
            message,
            format_favorites_header(len(products)),
            reply_markup=favorites_menu(prod_dicts),
        )

    @router.callback_query(F.data == "fav_list")
    async def cb_fav_list(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        user_id  = callback.from_user.id
        fav_keys = ctx.get_favorites(user_id)
        products  = [p for p in ctx.products if product_key(p) in fav_keys]

        if not products:
            await safe_send_message(
                callback,
                format_favorites_empty(),
                reply_markup=favorites_empty_menu(),
            )
        else:
            prod_dicts = [
                {"id": product_key(p), "name": p.name, "price": p.price or 0}
                for p in products
            ]
            await safe_send_message(
                callback,
                format_favorites_header(len(products)),
                reply_markup=favorites_menu(prod_dicts),
            )
        await callback.answer()

    @router.callback_query(F.data.startswith("fav:"))
    async def cb_fav_toggle(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        product_key_str = callback.data.split(":", 1)[1]
        user_id         = callback.from_user.id
        added           = ctx.toggle_favorite(user_id, product_key_str)

        if added:
            await callback.answer("❤️ Aggiunto ai preferiti!")
        else:
            await callback.answer("🤍 Rimosso dai preferiti.")

        # Aggiorna il bottone nella scheda prodotto
        product = get_product_by_key(product_key_str)
        if product:
            stock = int(getattr(product, "stock", 99))
            await callback.message.edit_reply_markup(
                reply_markup=product_card_menu(
                    product_key_str,
                    product.category or "",
                    stock,
                    added,
                )
            )

    # ─────────────────────────────────────────────────────────────
    #  PROFILO
    #  Reply keyboard: 👤 Profilo
    # ─────────────────────────────────────────────────────────────

    @router.message(F.text == BTN_PROFILO)
    async def my_profile(message: Message) -> None:
        if not message.from_user:
            return
        user_id  = message.from_user.id
        c_count  = cart_count(user_id)
        fav_count = len(ctx.get_favorites(user_id))
        await safe_send_message(
            message,
            format_profile(message.from_user, c_count, fav_count),
            reply_markup=profile_menu(),
        )

    # ─────────────────────────────────────────────────────────────
    #  NEGOZIO
    #  Reply keyboard: 📍 Negozio
    # ─────────────────────────────────────────────────────────────

    @router.message(F.text == BTN_NEGOZIO)
    async def store_info(message: Message) -> None:
        await safe_send_message(
            message,
            format_store_info(),
            reply_markup=store_menu(),
        )

    # ─────────────────────────────────────────────────────────────
    #  SUPPORTO
    #  Reply keyboard: 🎧 Supporto
    #  Callback: support, support_write, info_shipping
    # ─────────────────────────────────────────────────────────────

    @router.message(F.text == BTN_SUPPORTO)
    async def support(message: Message) -> None:
        await safe_send_message(
            message,
            format_support_info(),
            reply_markup=support_menu(),
        )

    @router.callback_query(F.data == "support")
    async def cb_support(callback: CallbackQuery) -> None:
        await safe_send_message(
            callback,
            format_support_info(),
            reply_markup=support_menu(),
        )
        await callback.answer()

    @router.callback_query(F.data == "support_write")
    async def cb_support_write(callback: CallbackQuery) -> None:
        if callback.from_user:
            record = customer_record(callback.from_user.id)
            record["stage"] = "support_collect"
            save_customer(callback.from_user.id, record)
        await safe_send_message(
            callback,
            "💬 Scrivi il tuo messaggio e lo invieremo al nostro team.\n"
            "Risposta garantita entro 2 ore."
        )
        await callback.answer()

    @router.callback_query(F.data == "info_shipping")
    async def cb_info_shipping(callback: CallbackQuery) -> None:
        await safe_send_message(
            callback,
            f"📦 <b>Informazioni spedizione</b>\n\n"
            f"✅ Spedizione gratuita da € {ctx.settings.free_shipping_min}\n"
            f"📦 Tariffa standard: € {ctx.settings.default_shipping}\n\n"
            f"🕐 Tempi di consegna: 2–4 giorni lavorativi\n"
            f"🏪 Ritiro in negozio disponibile gratuitamente",
        )
        await callback.answer()

    # ─────────────────────────────────────────────────────────────
    #  CERCA
    #  Reply keyboard: 🔍 Cerca
    # ─────────────────────────────────────────────────────────────

    @router.message(F.text == BTN_CERCA)
    async def search_start(message: Message) -> None:
        if not message.from_user:
            return
        record = customer_record(message.from_user.id)
        record["stage"] = "search_collect"
        save_customer(message.from_user.id, record)
        await safe_send_message(
            message,
            "🔍 Scrivi il nome del prodotto che cerchi:"
        )

    @router.callback_query(F.data == "search_again")
    async def cb_search_again(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        record = customer_record(callback.from_user.id)
        record["stage"] = "search_collect"
        save_customer(callback.from_user.id, record)
        await safe_send_message(
            callback,
            "🔍 Scrivi il nome del prodotto che cerchi:"
        )
        await callback.answer()

    # ─────────────────────────────────────────────────────────────
    #  Comandi testuali (invariati)
    # ─────────────────────────────────────────────────────────────

    @router.message(Command("contatti"))
    async def contacts(message: Message) -> None:
        await safe_send_message(
            message,
            format_company(ctx.company)
        )

    @router.message(Command("pagamenti"))
    async def payments_cmd(message: Message) -> None:
        await safe_send_message(
            message,
            format_payments(ctx.payment_methods, ctx.settings)
        )

    @router.message(Command("spedizione"))
    async def shipping_info(message: Message) -> None:
        await safe_send_message(
            message,
            f"📦 Spedizione gratuita da € {ctx.settings.free_shipping_min}.\n"
            f"Tariffa standard: € {ctx.settings.default_shipping}.\n"
            "Scrivimi paese e totale per un calcolo preciso."
        )

    @router.message(Command("b2b"))
    async def b2b(message: Message) -> None:
        if not message.from_user:
            return
        record = customer_record(message.from_user.id)
        record["type"]  = "b2b"
        record["stage"] = "qualify"
        save_customer(message.from_user.id, record)
        await safe_send_message(
            message,
            f"🏢 Profilo professionale attivato.\n"
            f"Sconto B2B: {ctx.settings.b2b_discount}%"
        )

    @router.message(Command("tracking"))
    async def tracking_cmd(message: Message) -> None:
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await safe_send_message(
                message,
                "Uso: /tracking <order_id>"
            )
            return
        shipments = ctx.store.load_json("shipments.json", {})
        entry     = shipments.get(parts[1].strip())
        if not entry:
            await safe_send_message(
                message,
                "Nessuna spedizione trovata per questo ordine."
            )
            return
        await safe_send_message(
            message,
            f"📦 Tracking <code>{parts[1].strip()}</code>:\n"
            f"Corriere: {entry.get('carrier')}\n"
            f"Codice: {entry.get('code')}\n"
            f"Stato: {entry.get('status')}\n"
            f"🔗 {entry.get('url')}",
        )

    @router.message(Command("faq"))
    async def faq_cmd(message: Message) -> None:
        if not ctx.faq:
            await safe_send_message(
                message,
                "FAQ non configurate."
            )
            return
        await safe_send_message(
            message,
            "FAQ:\n" + "\n".join(f"• {k}" for k in sorted(ctx.faq.keys()))
        )

    @router.message(Command("reset"))
    async def reset(message: Message) -> None:
        if message.from_user:
            record = customer_record(message.from_user.id)
            record.update({"stage": "idle", "followup_sent": False})
            save_customer(message.from_user.id, record)
        await safe_send_message(
            message,
            "Ripartiamo da zero. Dimmi cosa ti serve."
        )

    @router.message(Command("ordine"))
    async def order_entry(message: Message) -> None:
        if message.from_user:
            record = customer_record(message.from_user.id)
            record["stage"] = "order_collect"
            save_customer(message.from_user.id, record)
        await safe_send_message(
            message,
            "Perfetto. Inviami i dati del cliente e ti preparo totale, spedizione e Stripe."
        )

    # ─────────────────────────────────────────────────────────────
    #  Fallback testo libero
    # ─────────────────────────────────────────────────────────────

    @router.message(F.text)
    async def text_router(message: Message) -> None:
        if not message.from_user:
            return
        user_id = message.from_user.id
        record  = customer_record(user_id)
        record["chat_id"] = message.chat.id
        text    = message.text or ""

        # Aggiornamenti profilo da testo
        lang = detect_language(text)
        if lang and not record.get("lang"):
            record["lang"] = lang
        if detect_b2b(text):
            record["type"] = "b2b"
        pref = detect_preference(text)
        if pref:
            record["preference"] = pref
        fmt = detect_format(text)
        if fmt:
            record["format"] = fmt

        # Stage: raccolta coupon
        if record.get("stage") == "coupon_collect" and not text.startswith("/"):
            # Coupon semplice: codice fisso "WELCOME10" = 10%
            coupon    = text.strip().upper()
            discount  = 0.10 if coupon == "WELCOME10" else 0.0
            checkout  = ctx.get_checkout(user_id)
            checkout["coupon"]   = coupon
            checkout["discount"] = discount
            ctx.set_checkout(user_id, checkout)
            record["stage"] = "idle"
            save_customer(user_id, record)
            if discount > 0:
                await safe_send_message(
                    message,
                    f"🏷️ Coupon <b>{coupon}</b> applicato! Sconto del 10%.",
                )
            else:
                await safe_send_message(
                    message,
                    "❌ Coupon non valido."
                )
            return

        # Stage: raccolta query ricerca
        if record.get("stage") == "search_collect" and not text.startswith("/"):
            results = find_products(ctx.products, text)
            record["stage"] = "idle"
            save_customer(user_id, record)
            if not results:
                await safe_send_message(
                    message,
                    format_search_empty(text),
                    reply_markup=search_no_results_menu(),
                )
            else:
                prod_dicts = [
                    {"id": product_key(p), "name": p.name, "price": p.price or 0}
                    for p in results[:10]
                ]
                await safe_send_message(
                    message,
                    format_search_header(text, len(results)),
                    reply_markup=search_results_menu(prod_dicts),
                )
            return

        # Stage: raccolta dati ordine
        if record.get("stage") == "order_collect" and not text.startswith("/"):
            cart = get_cart(user_id)
            result = process_order_payload(
                message       = message,
                store         = ctx.store,
                products      = ctx.products,
                settings      = ctx.settings,
                cart          = cart,
                customer      = record,
                order_text    = text,
                shipping_rules= ctx.shipping_rules,
            )
            if not result:
                await safe_send_message(
                    message,
                    "Non capisco il totale. Scrivi prodotti, quantità e paese."
                )
                return

            record["stage"] = "payment_pending"
            record.setdefault("orders", []).append({
                "order_id": result.order_id,
                "total":    result.total,
                "status":   "pending",
                "ts":       int(time.time()),
            })
            record["next_followup"] = int(time.time() + ctx.settings.followup_hours * 3600)
            record["followup_sent"] = False
            save_customer(user_id, record)
            clear_cart(user_id)

            # Notifica admin
            for admin_id in ctx.settings.admin_chat_ids:
                try:
                    await message.bot.send_message(
                        admin_id,
                        f"🔔 Nuovo ordine #{result.order_id}\n"
                        f"@{message.from_user.username} | € {result.total:.2f}",
                    )
                except Exception:
                    pass

            ctx.store.append_jsonl("payments.jsonl", {
                "order_id": result.order_id,
                "status":   "pending",
                "user_id":  user_id,
                "username": message.from_user.username,
                "total":    result.total,
                "ts":       int(time.time()),
            })
            await safe_send_message(
                message,
                result.summary
            )

            upsell = recommend_upsell(ctx.products, result.subtotal, ctx.settings)
            if upsell:
                await safe_send_message(
                    message,
                    "💡 Se aggiungi uno di questi arrivi alla spedizione gratuita:\n"
                    + format_products(upsell, 3)
                )

            stripe_link = create_stripe_link(
                result.total, ctx.settings, f"Oro Naturale order {result.order_id}"
            )
            if stripe_link:
                await safe_send_message(
                    message,
                    f"💳 Pagamento Stripe:\n{stripe_link}"
                )
            return

        # Stage: messaggio al supporto
        if record.get("stage") == "support_collect" and not text.startswith("/"):
            record["stage"] = "idle"
            save_customer(user_id, record)
            for admin_id in ctx.settings.admin_chat_ids:
                try:
                    await message.bot.send_message(
                        admin_id,
                        f"🎧 <b>Supporto</b> da @{message.from_user.username}:\n{text}",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            await safe_send_message(
                message,
                "✅ Messaggio inviato al team. Ti risponderemo entro 2 ore."
            )
            return

        # Intento ordine libero
        if "voglio fare un ordine" in text.lower() or "ordine" in text.lower():
            record["stage"] = "order_collect"
            save_customer(user_id, record)
            await safe_send_message(
                message,
                "Perfetto! Dimmi:\n• Prodotti e quantità\n• Paese di destinazione\n• B2B o privato?"
            )
            return

        # FAQ
        for key, answer in ctx.faq.items():
            if key.lower() in text.lower():
                await safe_send_message(
                    message,
                    answer
                )
                save_customer(user_id, record)
                return

        # Raccomandazioni contestuali
        recommendations = recommendations_for(
            ctx.products, record.get("preference"), record.get("format")
        )
        if recommendations and any(
            w in text.lower() for w in ("olio", "catalogo", "prodotto", "consiglia")
        ):
            await safe_send_message(
                message,
                "🌿 Ti consiglio:\n" + format_products(recommendations)
            )
            save_customer(user_id, record)
            return

        # Risposta AI aziendale
        natural_reply = natural_business_reply(
            text           = text,
            products       = ctx.products,
            settings       = ctx.settings,
            shipping_rules = ctx.shipping_rules,
            company        = ctx.company,
        )
        if natural_reply:
            await safe_send_message(
                message,
                natural_reply
            )
            save_customer(user_id, record)
            return

        # Fallback generico
        save_customer(user_id, record)
        await safe_send_message(
            message,
            "Posso aiutarti con catalogo, carrello, spedizione, ordini e pagamenti.\n"
            "Usa il menu qui sotto o scrivi <i>voglio fare un ordine</i>.",
            reply_markup=main_menu(cart_count(user_id), ctx.settings.webapp_url),
        )

    return router