from __future__ import annotations

import asyncio
import time
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ..catalog import (
    CATEGORY_LABELS,
    category_label,
    find_products,
    format_product,
    format_products,
    group_by_category,
    recommendations_for,
    product_key,
)
from ..context import BotContext
from ..keyboards import categories_menu, cart_menu, main_menu, quantity_menu
from ..services import (
    create_stripe_link,
    detect_b2b,
    detect_format,
    detect_language,
    detect_preference,
    format_company,
    format_payments,
    is_admin_user,
    parse_total,
    process_order_payload,
    recommend_upsell,
)


def build_public_router(ctx: BotContext) -> Router:
    router = Router()

    def customer_record(user_id: int) -> dict:
        record = ctx.customers.get(str(user_id), {})
        record.setdefault("stage", "idle")
        record.setdefault("cart", {})
        return record

    def save_customer(user_id: int, record: dict) -> None:
        ctx.customers[str(user_id)] = record
        ctx.save_customers()

    def get_product(key: str):
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

    def add_to_cart(user_id: int, product_name: str, qty: int) -> None:
        cart = get_cart(user_id)
        cart[product_name] = cart.get(product_name, 0) + max(1, qty)
        set_cart(user_id, cart)

    def remove_from_cart(user_id: int, product_name: str) -> None:
        cart = get_cart(user_id)
        cart.pop(product_name, None)
        set_cart(user_id, cart)

    def clear_cart(user_id: int) -> None:
        set_cart(user_id, {})

    def cart_summary(user_id: int) -> str:
        cart = get_cart(user_id)
        if not cart:
            return "Il tuo carrello è vuoto."
        lines = ["Carrello:"]
        for key, qty in cart.items():
            product = get_product(key)
            if product and product.price:
                price = float(product.price.replace(",", "."))
                lines.append(f"- {product.name} x{qty} = EUR {price * qty:.2f}")
            else:
                lines.append(f"- {key} x{qty}")
        return "\n".join(lines)

    @router.message(Command("start"))
    async def start(message: Message) -> None:
        user_id = message.from_user.id if message.from_user else None
        if user_id:
            record = customer_record(user_id)
            record["chat_id"] = message.chat.id
            if not record.get("stage"):
                record["stage"] = "qualify"
            save_customer(user_id, record)
        await message.answer(
            "<b>Oro Naturale</b>\n"
            "Oli EVO, vini, cosmetici e confezioni regalo dall'Umbria.\n\n"
            "<b>Scorciatoie rapide</b>\n"
            "• catalogo e carrello\n"
            "• ordine e checkout Stripe\n"
            "• spedizione e tracking\n"
            "• area B2B per ristoratori\n\n"
            "Puoi anche scrivere direttamente <i>voglio fare un ordine</i>.",
            reply_markup=main_menu(),
            parse_mode="HTML",
        )

    @router.message(Command("help"))
    async def help_cmd(message: Message) -> None:
        await start(message)

    @router.message(F.text == "🛒 Catalogo")
    @router.message(Command("catalogo"))
    async def catalog(message: Message) -> None:
        groups = group_by_category(ctx.products)
        categories = [(k, category_label(k)) for k in groups.keys()]
        await message.answer(
            "Esplora le categorie disponibili:",
            reply_markup=categories_menu(categories),
        )

    @router.callback_query(F.data.startswith("cat:"))
    async def category(callback: CallbackQuery) -> None:
        category_name = callback.data.split(":", 1)[1]
        products = [p for p in ctx.products if p.category == category_name]
        if not products:
            await callback.answer("Nessun prodotto in questa categoria.")
            return
        await callback.message.answer(f"--- {category_label(category_name)} ---")
        for product in products[:10]:
            key = product_key(product)
            await callback.message.answer(
                format_product(product),
                reply_markup=quantity_menu(key, 1),
            )
        await callback.answer()

    @router.callback_query(F.data.startswith("qty:"))
    async def quantity(callback: CallbackQuery) -> None:
        _, product_id, qty_raw = callback.data.split(":", 2)
        qty = max(1, int(qty_raw))
        await callback.message.edit_reply_markup(
            reply_markup=quantity_menu(product_id, qty)
        )
        await callback.answer(f"Quantità: {qty}")

    @router.callback_query(F.data == "noop")
    async def noop(callback: CallbackQuery) -> None:
        await callback.answer()

    @router.callback_query(F.data.startswith("add:"))
    async def add(callback: CallbackQuery) -> None:
        _, product_id, qty_raw = callback.data.split(":", 2)
        qty = max(1, int(qty_raw))
        if callback.from_user:
            add_to_cart(callback.from_user.id, product_id, qty)
            await callback.answer(f"Aggiunto prodotto x{qty}")
        else:
            await callback.answer("Utente non trovato.")

    @router.message(F.text == "🛍️ Carrello")
    @router.message(Command("carrello"))
    async def cart(message: Message) -> None:
        if not message.from_user:
            return
        user_id = message.from_user.id
        cart_map = get_cart(user_id)
        if not cart_map:
            await message.answer("Il tuo carrello è vuoto. Usa /catalogo.")
            return
        cart_items = []
        for key in cart_map.keys():
            product = get_product(key)
            cart_items.append((product.name if product else key, key))
        await message.answer(
            cart_summary(user_id),
            reply_markup=cart_menu(cart_items),
        )

    @router.callback_query(F.data.startswith("rem:"))
    async def remove(callback: CallbackQuery) -> None:
        if callback.from_user:
            remove_from_cart(callback.from_user.id, callback.data.split(":", 1)[1])
            await callback.answer("Rimosso.")
            if callback.message:
                await cart(callback.message)

    @router.callback_query(F.data == "cart_clear")
    async def clear(callback: CallbackQuery) -> None:
        if callback.from_user:
            clear_cart(callback.from_user.id)
            await callback.answer("Carrello svuotato.")
            await callback.message.edit_text("Carrello svuotato. Usa /catalogo.")

    @router.callback_query(F.data == "checkout_data")
    async def checkout_data(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return
        record = customer_record(callback.from_user.id)
        record["stage"] = "order_collect"
        save_customer(callback.from_user.id, record)
        await callback.message.answer(
            "Per completare l'ordine, scrivimi in un solo messaggio:\n"
            "- Nome e cognome\n"
            "- Indirizzo completo\n"
            "- Email\n"
            "- Eventuale Partita IVA\n"
            "Poi ti mando totale e checkout Stripe."
        )
        await callback.answer()

    @router.message(Command("contatti"))
    async def contacts(message: Message) -> None:
        await message.answer(format_company(ctx.company))

    @router.message(F.text == "📞 Contatti")
    async def contacts_button(message: Message) -> None:
        await contacts(message)

    @router.message(Command("pagamenti"))
    async def payments(message: Message) -> None:
        await message.answer(format_payments(ctx.payment_methods, ctx.settings))

    @router.message(F.text == "💳 Pagamenti")
    async def payments_button(message: Message) -> None:
        await payments(message)

    @router.message(Command("spedizione"))
    async def shipping_info(message: Message) -> None:
        await message.answer(
            f"Spedizione gratuita da EUR {ctx.settings.free_shipping_min}.\n"
            f"Tariffa standard: EUR {ctx.settings.default_shipping}.\n"
            "Scrivimi paese e totale ordine per un calcolo preciso."
        )

    @router.message(Command("b2b"))
    async def b2b(message: Message) -> None:
        if not message.from_user:
            return
        record = customer_record(message.from_user.id)
        record["type"] = "b2b"
        record["stage"] = "qualify"
        save_customer(message.from_user.id, record)
        await message.answer(
            f"Attivato profilo professionale con sconto del {ctx.settings.b2b_discount}%."
        )

    @router.message(F.text == "🏢 Area B2B")
    async def b2b_button(message: Message) -> None:
        await b2b(message)

    @router.message(Command("lingua"))
    async def language(message: Message) -> None:
        parts = (message.text or "").split()
        if len(parts) < 2:
            await message.answer("Uso: /lingua it|en|de")
            return
        code = parts[1].lower()
        if code not in {"it", "en", "de"}:
            await message.answer("Lingua non supportata.")
            return
        if message.from_user:
            record = customer_record(message.from_user.id)
            record["lang"] = code
            save_customer(message.from_user.id, record)
        await message.answer(f"Lingua impostata: {code}")

    @router.message(Command("faq"))
    async def faq(message: Message) -> None:
        if not ctx.faq:
            await message.answer("FAQ non configurate.")
            return
        await message.answer("FAQ:\n" + "\n".join(f"- {k}" for k in sorted(ctx.faq.keys())))

    @router.message(F.text == "ℹ️ Info & FAQ")
    async def faq_button(message: Message) -> None:
        await faq(message)

    @router.message(Command("tracking"))
    async def tracking(message: Message) -> None:
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Uso: /tracking <order_id>")
            return
        shipments = ctx.store.load_json("shipments.json", {})
        entry = shipments.get(parts[1].strip())
        if not entry:
            await message.answer("Nessuna spedizione trovata per questo ordine.")
            return
        await message.answer(
            f"Tracking {parts[1].strip()}:\n"
            f"Corriere: {entry.get('carrier')}\n"
            f"Codice: {entry.get('code')}\n"
            f"Stato: {entry.get('status')}\n"
            f"Link: {entry.get('url')}"
        )

    @router.message(F.text == "📦 Spedizione")
    async def shipping_button(message: Message) -> None:
        await shipping_info(message)

    @router.message(Command("reset"))
    async def reset(message: Message) -> None:
        if message.from_user:
            record = customer_record(message.from_user.id)
            record.update({"stage": "idle", "followup_sent": False})
            save_customer(message.from_user.id, record)
        await message.answer("Ripartiamo da zero. Dimmi cosa ti serve.")

    @router.message(Command("ordine"))
    async def order_entry(message: Message) -> None:
        if message.from_user:
            record = customer_record(message.from_user.id)
            record["stage"] = "order_collect"
            save_customer(message.from_user.id, record)
        await message.answer(
            "Perfetto. Inviami i dati del cliente e ti preparo totale, spedizione e Stripe."
        )

    @router.message(F.text == "📝 Fai un ordine")
    async def order_button(message: Message) -> None:
        await order_entry(message)

    @router.message(F.text)
    async def text_router(message: Message) -> None:
        if not message.from_user:
            return
        record = customer_record(message.from_user.id)
        record["chat_id"] = message.chat.id
        lang = detect_language(message.text or "")
        if lang and not record.get("lang"):
            record["lang"] = lang

        if detect_b2b(message.text or ""):
            record["type"] = "b2b"

        pref = detect_preference(message.text or "")
        if pref:
            record["preference"] = pref

        fmt = detect_format(message.text or "")
        if fmt:
            record["format"] = fmt

        if record.get("stage") == "order_collect" and not (message.text or "").startswith("/"):
            cart = get_cart(message.from_user.id)
            result = process_order_payload(
                message=message,
                store=ctx.store,
                products=ctx.products,
                settings=ctx.settings,
                cart=cart,
                customer=record,
                order_text=message.text or "",
                shipping_rules=ctx.shipping_rules,
            )
            if not result:
                await message.answer("Non capisco il totale. Scrivi prodotti, quantità e paese.")
                return
            record["stage"] = "payment_pending"
            record.setdefault("orders", []).append(
                {"order_id": result.order_id, "total": result.total, "ts": int(time.time())}
            )
            record["next_followup"] = int(time.time() + ctx.settings.followup_hours * 3600)
            record["followup_sent"] = False
            save_customer(message.from_user.id, record)
            set_cart(message.from_user.id, {})
            for admin_id in ctx.settings.admin_chat_ids:
                await message.bot.send_message(
                    admin_id,
                    "Nuovo ordine:\n"
                    f"ID: {result.order_id}\n"
                    f"Utente: @{message.from_user.username}\n"
                    f"Totale: EUR {result.total:.2f}\n"
                    f"Paese: {result.country}\n"
                    f"Stato: payment_pending",
                )
            ctx.store.append_jsonl(
                "payments.jsonl",
                {
                    "order_id": result.order_id,
                    "status": "pending",
                    "user_id": message.from_user.id,
                    "username": message.from_user.username,
                    "total": result.total,
                    "ts": int(time.time()),
                },
            )
            await message.answer(result.summary)
            upsell = recommend_upsell(ctx.products, result.subtotal, ctx.settings)
            if upsell:
                await message.answer(
                    "Se aggiungi uno di questi arrivi alla spedizione gratuita:\n"
                    + format_products(upsell, 3)
                )
            stripe_link = create_stripe_link(
                result.total, ctx.settings, f"Oro Naturale order {result.order_id}"
            )
            if stripe_link:
                await message.answer(f"Pagamento Stripe:\n{stripe_link}")
            return

        if message.text and "voglio fare un ordine" in message.text.lower():
            record["stage"] = "order_collect"
            save_customer(message.from_user.id, record)
            await message.answer(
                "Perfetto. Dimmi:\n- Prodotti e quantità\n- Paese/città\n- Se sei B2B o privato"
            )
            return

        for key, answer in ctx.faq.items():
            if key.lower() in (message.text or "").lower():
                await message.answer(answer)
                save_customer(message.from_user.id, record)
                return

        recommendations = recommendations_for(ctx.products, record.get("preference"), record.get("format"))
        if recommendations and ("olio" in (message.text or "").lower() or "catalogo" in (message.text or "").lower()):
            await message.answer("Ti consiglio:\n" + format_products(recommendations))
            save_customer(message.from_user.id, record)
            return

        await message.answer(
            "Posso aiutarti con catalogo, carrello, spedizione, ordini e pagamenti Stripe.\n"
            "Usa il menu qui sotto oppure scrivi <i>voglio fare un ordine</i>.",
            parse_mode="HTML",
        )
        save_customer(message.from_user.id, record)

    return router
