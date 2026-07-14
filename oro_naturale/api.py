# ═══════════════════════════════════════════════════════════════════
#  Oro Naturale — API HTTP della Mini App
#
#  Endpoint (montati su /api dal web server):
#    GET  /api/config                     → config pubblica per la mini app
#    POST /api/orders                     → crea ordine + ordine Revolut
#    POST /api/orders/{id}/confirm        → verifica pagamento e conferma
#    GET  /api/profile                    → ordini + profilo dell'utente
#    GET  /api/admin/orders               → tutti gli ordini (solo admin)
#    POST /api/admin/orders/{id}/tracking → imposta tracking (solo admin)
#    POST /api/revolut/webhook            → conferma pagamento lato Revolut
#
#  L'utente è autenticato validando initData di Telegram (header
#  X-Init-Data o campo init_data nel body). I prezzi sono ricalcolati
#  server-side dal catalogo: il client non può manometterli.
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import itertools
import logging
import secrets
import time
from typing import Any

from aiohttp import web

from . import db
from .revolut import RevolutError, build_client, is_paid
from .webauth import validate_init_data

logger = logging.getLogger(__name__)

# Sequenza monotona (atomica per il GIL) + tag casuale per processo/istanza:
# garantisce ID ordine univoci anche con più utenti che acquistano nello stesso
# istante — `next()` è strettamente crescente e `_PROC_TAG` distingue i riavvii
# e le eventuali repliche. L'id è PRIMARY KEY.
_ORDER_SEQ = itertools.count(1)
_PROC_TAG = secrets.token_hex(2).upper()


def _order_id() -> str:
    return f"ON-{int(time.time())}-{_PROC_TAG}-{next(_ORDER_SEQ):06d}"


# Fasce di spedizione allineate a biomarketshop.com.
_NORDIC = {"SE", "NO", "DK", "FI", "IS"}
_EUROPE = {"IT", "FR", "ES", "DE", "AT", "BE", "NL", "PT", "GR", "IE", "LU", "CH", "GB"}


def _compute_shipping(subtotal: float, country: str, settings: Any) -> float:
    """Costo di spedizione: gratis oltre soglia, poi in base al paese (ISO-2)."""
    if subtotal >= settings.free_shipping_min:
        return 0.0
    c = (country or "IT").upper()
    if c in _NORDIC:
        return 14.0
    if c in _EUROPE:
        return float(settings.default_shipping)
    return 25.0


def _price_index(products: list) -> dict[str, dict]:
    """Indice id → {name, price, stock} dal catalogo (Product o dict)."""
    index: dict[str, dict] = {}
    for p in products:
        pid = getattr(p, "id", None) if not isinstance(p, dict) else p.get("id")
        name = getattr(p, "name", None) if not isinstance(p, dict) else p.get("name")
        price = getattr(p, "price", None) if not isinstance(p, dict) else p.get("price")
        stock = getattr(p, "stock", 0) if not isinstance(p, dict) else p.get("stock", 0)
        if pid:
            try:
                index[str(pid)] = {"name": name or "Prodotto", "price": float(price or 0), "stock": int(stock or 0)}
            except (TypeError, ValueError):
                continue
    return index


def build_api(ctx: Any, bot: Any = None) -> web.Application:
    """
    Crea la sub-app API. `ctx` espone .settings e .products; `bot` (opzionale)
    è l'istanza aiogram per le notifiche Telegram.
    """
    settings = ctx.settings
    app = web.Application()

    # ── helpers auth ──────────────────────────────────────────────

    async def _read_body(request: web.Request) -> dict:
        if request.can_read_body:
            try:
                return await request.json()
            except Exception:
                return {}
        return {}

    def _init_data(request: web.Request, body: dict) -> str:
        return (
            request.headers.get("X-Init-Data")
            or request.headers.get("X-Telegram-Init-Data")
            or (body.get("init_data") if isinstance(body, dict) else "")
            or ""
        )

    def _auth_user(request: web.Request, body: dict) -> dict | None:
        data = validate_init_data(_init_data(request, body), settings.telegram_bot_token)
        if not data:
            return None
        return data.get("user") or None

    def _is_admin(user: dict | None) -> bool:
        return bool(user and int(user.get("id", 0)) in settings.admin_chat_ids)

    async def _notify(chat_id: int, text: str) -> None:
        if bot is None:
            return
        try:
            await bot.send_message(chat_id, text, parse_mode="HTML")
        except Exception as exc:  # noqa: BLE001
            logger.warning("notify %s fallita: %s", chat_id, exc)

    # ── GET /config ───────────────────────────────────────────────

    async def config(request: web.Request) -> web.Response:
        body: dict = {}
        user = _auth_user(request, body)
        return web.json_response({
            "revolut_public_key": settings.revolut_public_key,
            "revolut_mode": settings.revolut_mode,
            "revolut_enabled": bool(settings.revolut_secret_key and settings.revolut_public_key),
            "paypal_enabled": bool(settings.paypal_email),
            "paypal_email": settings.paypal_email,
            "currency": (settings.stripe_currency or "eur").upper(),
            "free_shipping_min": settings.free_shipping_min,
            "default_shipping": settings.default_shipping,
            "is_admin": _is_admin(user),
        })

    # ── POST /orders ──────────────────────────────────────────────

    async def create_order(request: web.Request) -> web.Response:
        body = await _read_body(request)
        user = _auth_user(request, body)
        if not user:
            return web.json_response({"error": "unauthorized"}, status=401)

        items_in = body.get("items") or []
        shipping_in = body.get("shipping") or {}
        if not items_in:
            return web.json_response({"error": "carrello vuoto"}, status=400)

        index = _price_index(ctx.products)
        items: list[dict] = []
        subtotal = 0.0
        for it in items_in:
            pid = str(it.get("id", ""))
            qty = max(1, int(it.get("quantity", 1)))
            prod = index.get(pid)
            if not prod:
                return web.json_response({"error": f"prodotto non valido: {pid}"}, status=400)
            line = round(prod["price"] * qty, 2)
            subtotal += line
            items.append({"id": pid, "name": prod["name"], "price": prod["price"], "quantity": qty})

        subtotal = round(subtotal, 2)
        country = shipping_in.get("country") or "IT"
        shipping = round(_compute_shipping(subtotal, country, settings), 2)
        total = round(subtotal + shipping, 2)
        currency = (settings.stripe_currency or "eur").upper()
        oid = _order_id()

        # Aggiorna/crea il profilo cliente con i dati di spedizione
        await asyncio.to_thread(
            db.upsert_customer, int(user["id"]),
            username=user.get("username"), first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            phone=shipping_in.get("phone"), address=shipping_in.get("address"),
            city=shipping_in.get("city"), zip_code=shipping_in.get("zip"),
        )

        payment_method = (body.get("payment_method") or "revolut").lower()
        base_order = {
            "id": oid, "user_id": int(user["id"]), "username": user.get("username"),
            "items": items, "subtotal": subtotal, "shipping": shipping, "total": total,
            "currency": currency,
            "shipping_name": shipping_in.get("name"), "shipping_phone": shipping_in.get("phone"),
            "shipping_address": shipping_in.get("address"), "shipping_city": shipping_in.get("city"),
            "shipping_zip": shipping_in.get("zip"), "shipping_notes": shipping_in.get("notes"),
        }

        # ── PayPal: ordine "in attesa di pagamento" (pagamento manuale) ──
        if payment_method == "paypal":
            if not settings.paypal_email:
                return web.json_response({"error": "PayPal non configurato"}, status=400)
            order = {
                **base_order, "status": "awaiting_payment",
                "payment_method": "paypal", "payment_provider": "paypal",
            }
            await asyncio.to_thread(db.create_order, order)
            await _notify_admins_new_order(await asyncio.to_thread(db.get_order, oid) or order, paid=False)
            pm = settings.paypal_me
            if pm and not pm.startswith("http"):
                pm = "https://" + pm.lstrip("/")
            return web.json_response({
                "order_id": oid, "total": total, "subtotal": subtotal, "shipping": shipping,
                "currency": currency, "payment_method": "paypal",
                "paypal_email": settings.paypal_email,
                "paypal_link": f"{pm.rstrip('/')}/{total:.2f}EUR" if pm else None,
            })

        # ── Revolut (default) ──
        revolut_token = None
        revolut_order_id = None
        client = build_client(settings.revolut_secret_key, settings.revolut_mode, settings.revolut_api_version)
        if client is not None:
            try:
                rev = await client.create_order(
                    amount_minor=int(round(total * 100)),
                    currency=currency,
                    merchant_order_ext_ref=oid,
                    description=f"Oro Naturale {oid}",
                )
                revolut_token = rev.get("token")
                revolut_order_id = rev.get("id")
            except RevolutError as exc:
                logger.error("create Revolut order fallita: %s", exc)
                return web.json_response({"error": "pagamento non disponibile", "detail": str(exc)}, status=502)

        order = {
            **base_order, "status": "pending",
            "payment_method": None, "payment_provider": "revolut" if client else None,
            "revolut_order_id": revolut_order_id,
        }
        await asyncio.to_thread(db.create_order, order)

        return web.json_response({
            "order_id": oid,
            "total": total,
            "subtotal": subtotal,
            "shipping": shipping,
            "currency": currency,
            "payment_method": "revolut",
            "revolut_token": revolut_token,
            "revolut_public_key": settings.revolut_public_key,
            "revolut_mode": settings.revolut_mode,
        })

    # ── POST /orders/{id}/confirm ─────────────────────────────────

    async def confirm_order(request: web.Request) -> web.Response:
        body = await _read_body(request)
        user = _auth_user(request, body)
        if not user:
            return web.json_response({"error": "unauthorized"}, status=401)

        oid = request.match_info["id"]
        order = await asyncio.to_thread(db.get_order, oid)
        if not order or int(order.get("user_id") or 0) != int(user["id"]):
            return web.json_response({"error": "ordine non trovato"}, status=404)

        if order["status"] == "paid":
            return web.json_response({"order": order, "paid": True})

        method = body.get("payment_method")
        paid = False
        client = build_client(settings.revolut_secret_key, settings.revolut_mode, settings.revolut_api_version)
        if client is not None and order.get("revolut_order_id"):
            try:
                rev = await client.get_order(order["revolut_order_id"])
                paid = is_paid(rev)
            except RevolutError as exc:
                logger.warning("verifica Revolut fallita per %s: %s", oid, exc)

        if paid:
            updated = await asyncio.to_thread(
                db.update_order_status, oid, "paid", mark_paid=True, payment_method=method or "revolut",
            )
            await _notify_admins_new_order(updated or order)
            return web.json_response({"order": updated or order, "paid": True})

        return web.json_response({"order": order, "paid": False})

    async def _notify_admins_new_order(order: dict, paid: bool = True) -> None:
        items_txt = "\n".join(
            f"  • {i.get('quantity')}× {i.get('name')}" for i in (order.get("items") or [])
        )
        header = (
            "🔔 <b>NUOVO ORDINE PAGATO</b>" if paid
            else "🟡 <b>NUOVO ORDINE — PayPal DA CONFERMARE</b>"
        )
        text = (
            f"{header} <code>#{order['id']}</code>\n"
            f"👤 {order.get('shipping_name') or '—'} (@{order.get('username') or order.get('user_id')})\n"
            f"📞 {order.get('shipping_phone') or '—'}\n"
            f"📍 {order.get('shipping_address') or ''}, {order.get('shipping_zip') or ''} {order.get('shipping_city') or ''}\n"
            f"💳 {order.get('payment_method') or 'revolut'}\n"
            f"{items_txt}\n"
            f"💰 <b>€ {float(order.get('total', 0)):.2f}</b>"
        )
        for admin_id in settings.admin_chat_ids:
            await _notify(admin_id, text)

    # ── GET /profile ──────────────────────────────────────────────

    async def profile(request: web.Request) -> web.Response:
        user = _auth_user(request, {})
        if not user:
            return web.json_response({"error": "unauthorized"}, status=401)
        uid = int(user["id"])
        orders = await asyncio.to_thread(db.list_user_orders, uid)
        customer = await asyncio.to_thread(db.get_customer, uid)
        return web.json_response({"customer": customer, "orders": orders})

    # ── POST /profile/clear-pending ───────────────────────────────

    async def clear_pending(request: web.Request) -> web.Response:
        """Svuota gli ordini non pagati (pending) dell'utente."""
        user = _auth_user(request, {})
        if not user:
            return web.json_response({"error": "unauthorized"}, status=401)
        uid = int(user["id"])
        removed = await asyncio.to_thread(db.delete_pending_orders, uid)
        orders = await asyncio.to_thread(db.list_user_orders, uid)
        return web.json_response({"removed": removed, "orders": orders})

    # ── GET /admin/orders (solo ordini pagati) ────────────────────

    async def admin_orders(request: web.Request) -> web.Response:
        user = _auth_user(request, {})
        if not _is_admin(user):
            return web.json_response({"error": "forbidden"}, status=403)
        # exclude_pending=True (default): l'admin vede solo ordini pagati
        orders = await asyncio.to_thread(db.list_all_orders)
        return web.json_response({"orders": orders})

    # ── POST /admin/orders/{id}/tracking ──────────────────────────

    async def admin_set_tracking(request: web.Request) -> web.Response:
        body = await _read_body(request)
        user = _auth_user(request, body)
        if not _is_admin(user):
            return web.json_response({"error": "forbidden"}, status=403)

        oid = request.match_info["id"]
        carrier = (body.get("carrier") or "").strip()
        code = (body.get("code") or "").strip()
        url = (body.get("url") or "").strip() or None
        status = (body.get("status") or "shipped").strip()
        if not carrier or not code:
            return web.json_response({"error": "carrier e code obbligatori"}, status=400)

        updated = await asyncio.to_thread(
            db.set_tracking, oid, carrier=carrier, code=code, url=url, status=status,
        )
        if not updated:
            return web.json_response({"error": "ordine non trovato"}, status=404)

        if updated.get("user_id"):
            link = f"\n🔗 {url}" if url else ""
            await _notify(
                int(updated["user_id"]),
                f"📦 <b>Il tuo ordine</b> <code>#{oid}</code> è stato spedito!\n"
                f"Corriere: <b>{carrier}</b>\nCodice: <code>{code}</code>{link}",
            )
        return web.json_response({"order": updated})

    # ── POST /admin/orders/{id}/status ────────────────────────────

    ALLOWED_STATUS = {"pending", "awaiting_payment", "paid", "preparing", "shipped", "delivered", "cancelled"}
    STATUS_MSG = {
        "preparing": "🧑‍🍳 Il tuo ordine <code>#{id}</code> è <b>in preparazione</b>.",
        "delivered": "✅ Il tuo ordine <code>#{id}</code> è stato <b>consegnato</b>. Grazie!",
        "cancelled": "❌ Il tuo ordine <code>#{id}</code> è stato <b>annullato</b>. Contatta il supporto per assistenza.",
    }

    async def admin_set_status(request: web.Request) -> web.Response:
        body = await _read_body(request)
        user = _auth_user(request, body)
        if not _is_admin(user):
            return web.json_response({"error": "forbidden"}, status=403)

        oid = request.match_info["id"]
        status = (body.get("status") or "").strip()
        if status not in ALLOWED_STATUS:
            return web.json_response({"error": "stato non valido"}, status=400)

        updated = await asyncio.to_thread(db.update_order_status, oid, status)
        if not updated:
            return web.json_response({"error": "ordine non trovato"}, status=404)

        msg = STATUS_MSG.get(status)
        if msg and updated.get("user_id"):
            await _notify(int(updated["user_id"]), msg.format(id=oid))
        return web.json_response({"order": updated})

    # ── POST /revolut/webhook ─────────────────────────────────────

    async def revolut_webhook(request: web.Request) -> web.Response:
        body = await _read_body(request)
        # Non ci fidiamo del payload: verifichiamo lo stato con Revolut.
        rev_order_id = (body.get("order_id") or (body.get("data") or {}).get("id"))
        if not rev_order_id:
            return web.json_response({"ok": True})
        client = build_client(settings.revolut_secret_key, settings.revolut_mode, settings.revolut_api_version)
        if client is None:
            return web.json_response({"ok": True})
        try:
            rev = await client.get_order(str(rev_order_id))
        except RevolutError:
            return web.json_response({"ok": True})
        if is_paid(rev):
            ext_ref = rev.get("merchant_order_ext_ref")
            if ext_ref:
                order = await asyncio.to_thread(db.get_order, ext_ref)
                if order and order["status"] != "paid":
                    updated = await asyncio.to_thread(
                        db.update_order_status, ext_ref, "paid", mark_paid=True, payment_method="revolut",
                    )
                    await _notify_admins_new_order(updated or order)
        return web.json_response({"ok": True})

    app.router.add_get("/config", config)
    app.router.add_post("/orders", create_order)
    app.router.add_post("/orders/{id}/confirm", confirm_order)
    app.router.add_get("/profile", profile)
    app.router.add_post("/profile/clear-pending", clear_pending)
    app.router.add_get("/admin/orders", admin_orders)
    app.router.add_post("/admin/orders/{id}/tracking", admin_set_tracking)
    app.router.add_post("/admin/orders/{id}/status", admin_set_status)
    app.router.add_post("/revolut/webhook", revolut_webhook)
    return app
