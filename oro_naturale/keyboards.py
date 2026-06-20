"""
╔══════════════════════════════════════════════════════════════════╗
║             MioNegozio — Telegram Shop Bot                      ║
║             aiogram v3 | FSM | Inline + Reply Keyboard          ║
╚══════════════════════════════════════════════════════════════════╝

Struttura replicata dall'ideogramma:
  ┌─ /start          → Benvenuto + Reply Keyboard (8 tasti)
  ├─ 🛍️ Catalogo     → Categorie inline (2×3 grid + Offerte)
  │    └─ Prodotto   → Scheda + [Aggiungi | Salva] [Dettagli | Indietro]
  ├─ 🛒 Carrello     → Riepilogo ordine + [Procedi] [Modifica | Coupon] [Svuota | +Prodotti]
  │    ├─ Spedizione → [Spedizione a casa] [Ritiro in negozio]
  │    └─ Pagamento  → [Paga ora] [Bonifico | PayPal]
  ├─ 🔍 Cerca        → Prompt testo → risultati inline
  ├─ 📦 Ordini       → Lista ordini + tracking
  ├─ ❤️ Preferiti    → Lista salvati
  ├─ 👤 Profilo      → Dati utente
  ├─ 📍 Negozio      → Info + mappa
  └─ 🎧 Supporto     → Contatto operatore

Dipendenze:
    pip install aiogram==3.* python-dotenv

Variabili d'ambiente (.env):
    BOT_TOKEN=your_token_here
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "INSERISCI_QUI_IL_TOKEN")

# ═══════════════════════════════════════════════════════════════════
#  DATI MOCK — sostituire con DB reale (PostgreSQL / SQLite)
# ═══════════════════════════════════════════════════════════════════

CATEGORIES = {
    "abbigliamento": ("👕", "Abbigliamento"),
    "scarpe":        ("👟", "Scarpe"),
    "accessori":     ("🎒", "Accessori"),
    "casa":          ("🏠", "Casa"),
    "tech":          ("🎮", "Tech"),
    "beauty":        ("🌿", "Beauty"),
}

PRODUCTS = {
    "tshirt_001": {
        "name": "T-Shirt Premium Essentials",
        "emoji": "👕",
        "category": "abbigliamento",
        "price": 24.90,
        "old_price": 34.90,
        "description": "100% cotone organico — Taglia S/M/L/XL",
        "rating": 4.8,
        "reviews": 124,
        "badge": "NEW",
    },
    "sneaker_001": {
        "name": "Sneakers Urban Pro",
        "emoji": "👟",
        "category": "scarpe",
        "price": 89.00,
        "old_price": 119.00,
        "description": "Suola in gomma vulcanizzata — 38/46",
        "rating": 4.5,
        "reviews": 67,
        "badge": "SALE",
    },
    "bag_001": {
        "name": "Zaino Explorer 30L",
        "emoji": "🎒",
        "category": "accessori",
        "price": 59.90,
        "old_price": None,
        "description": "Impermeabile, vano laptop 15'' — Nero/Grigio",
        "rating": 4.9,
        "reviews": 203,
        "badge": None,
    },
}

SHIPPING_OPTIONS = {
    "home":    ("📦", "Spedizione a casa", 4.90),
    "pickup":  ("🏪", "Ritiro in negozio",  0.00),
}

PAYMENT_OPTIONS = {
    "card":    ("💳", "Carta di credito / Telegram Pay"),
    "bank":    ("🏦", "Bonifico bancario"),
    "paypal":  ("💸", "PayPal"),
}

# Carrelli in memoria: {user_id: {product_id: qty}}
# In produzione → Redis / DB
carts: dict[int, dict[str, int]] = {}
favorites: dict[int, set[str]] = {}
discount_codes = {"BENVENUTO10": 0.10, "ESTATE20": 0.20}


# ═══════════════════════════════════════════════════════════════════
#  FSM STATES
# ═══════════════════════════════════════════════════════════════════

class ShopFSM(StatesGroup):
    # Navigazione catalogo
    browsing_category = State()
    viewing_product   = State()

    # Checkout
    cart_review       = State()
    entering_coupon   = State()
    choosing_shipping = State()
    choosing_payment  = State()
    entering_address  = State()

    # Ricerca
    searching         = State()

    # Supporto
    support_message   = State()


# ═══════════════════════════════════════════════════════════════════
#  ─────────────────── KEYBOARDS ───────────────────────────────────
# ═══════════════════════════════════════════════════════════════════

# ── REPLY KEYBOARD (barra fissa) ──────────────────────────────────

def reply_main_menu(cart_count: int = 0) -> ReplyKeyboardMarkup:
    """
    Menu principale fisso — 4 righe × 2 colonne.
    Regola: macro-navigazione sempre accessibile.
    """
    cart_label = f"🛒 Carrello ({cart_count})" if cart_count > 0 else "🛒 Carrello"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Catalogo"),   KeyboardButton(text="🔍 Cerca")],
            [KeyboardButton(text=cart_label),       KeyboardButton(text="📦 I miei ordini")],
            [KeyboardButton(text="❤️ Preferiti"),  KeyboardButton(text="👤 Profilo")],
            [KeyboardButton(text="📍 Negozio"),     KeyboardButton(text="🎧 Supporto")],
        ],
        resize_keyboard=True,
        is_persistent=True,          # rimane visibile tra i messaggi
    )


def reply_back_only() -> ReplyKeyboardMarkup:
    """Mini keyboard con solo torna al menu — usata in stati intermedi."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Menu principale")]],
        resize_keyboard=True,
    )


# ── INLINE KEYBOARDS ──────────────────────────────────────────────

def ikb(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    """Helper: costruisce InlineKeyboardMarkup da righe di bottoni."""
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


def btn(text: str, data: str) -> InlineKeyboardButton:
    """Shorthand per bottone callback."""
    return InlineKeyboardButton(text=text, callback_data=data)


def btn_url(text: str, url: str) -> InlineKeyboardButton:
    """Shorthand per bottone URL esterno."""
    return InlineKeyboardButton(text=text, url=url)


# ── Categorie ──

def kb_categories() -> InlineKeyboardMarkup:
    """
    Griglia categorie: 2 bottoni per riga + Offerte full-width.
    Max 3 righe standard + 1 riga CTA.
    """
    rows = []
    cats = list(CATEGORIES.items())
    for i in range(0, len(cats), 2):
        row = []
        for key, (emoji, label) in cats[i:i+2]:
            row.append(btn(f"{emoji} {label}", f"cat:{key}"))
        rows.append(row)
    rows.append([btn("🔥 Offerte del giorno", "cat:offerte")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Scheda prodotto ──

def kb_product(product_id: str, is_fav: bool = False) -> InlineKeyboardMarkup:
    """
    Anatomia pulsantiera prodotto (3 righe):
    Riga 1 — Primario: Aggiungi al carrello (verde, full-width)
    Riga 2 — Secondari: [Salva ❤️ | Dettagli ℹ️]
    Riga 3 — Navigazione: [◀ Categoria | 🔙 Menu]
    """
    fav_label = "❤️ Salvato" if is_fav else "🤍 Salva"
    return ikb(
        [btn("🛒 Aggiungi al carrello", f"add:{product_id}")],
        [btn(fav_label, f"fav:{product_id}"), btn("ℹ️ Dettagli", f"info:{product_id}")],
        [btn("◀ Torna alla categoria", f"back_cat:{product_id}"),
         btn("🏠 Menu", "main_menu")],
    )


# ── Lista prodotti categoria ──

def kb_product_list(product_ids: list[str], category: str) -> InlineKeyboardMarkup:
    """Un bottone per prodotto + pulsante indietro."""
    rows = []
    for pid in product_ids:
        p = PRODUCTS[pid]
        price_str = f"€{p['price']:.2f}"
        badge = f" [{p['badge']}]" if p.get("badge") else ""
        rows.append([btn(f"{p['emoji']} {p['name']} — {price_str}{badge}", f"prod:{pid}")])
    rows.append([btn("◀ Categorie", "show_categories"), btn("🔙 Menu", "main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Carrello ──

def kb_cart(has_items: bool = True) -> InlineKeyboardMarkup:
    """
    Pulsantiera carrello:
    Riga 1 — Primario: Procedi al checkout (verde)
    Riga 2 — [Modifica quantità | Inserisci coupon]
    Riga 3 — [🗑️ Svuota | 🛍️ Continua acquisti]
    """
    if not has_items:
        return ikb(
            [btn("🛍️ Vai al catalogo", "show_categories")],
        )
    return ikb(
        [btn("✅ Procedi al checkout", "checkout_start")],
        [btn("✏️ Modifica quantità",   "cart_edit"),
         btn("🏷️ Inserisci coupon",    "cart_coupon")],
        [btn("🗑️ Svuota carrello",     "cart_clear"),
         btn("🛍️ Continua acquisti",   "show_categories")],
    )


# ── Spedizione ──

def kb_shipping() -> InlineKeyboardMarkup:
    """
    Riga 1 — [📦 Spedizione a casa] (primario)
    Riga 2 — [🏪 Ritiro in negozio]
    Riga 3 — [◀ Torna al carrello]
    """
    return ikb(
        [btn("📦 Spedizione a casa  (+€4,90)",  "ship:home")],
        [btn("🏪 Ritiro in negozio (gratuito)", "ship:pickup")],
        [btn("◀ Torna al carrello",             "show_cart")],
    )


# ── Pagamento ──

def kb_payment(total: float) -> InlineKeyboardMarkup:
    """
    Riga 1 — Primario: Paga ora con totale (verde)
    Riga 2 — [Bonifico | PayPal]
    Riga 3 — [◀ Spedizione]
    """
    return ikb(
        [btn(f"💳 Paga ora — €{total:.2f}", "pay:card")],
        [btn("🏦 Bonifico bancario", "pay:bank"),
         btn("💸 PayPal",            "pay:paypal")],
        [btn("◀ Modifica spedizione", "checkout_start")],
    )


# ── Conferma ordine ──

def kb_order_confirmed(order_id: str) -> InlineKeyboardMarkup:
    return ikb(
        [btn("📦 Traccia spedizione", f"track:{order_id}")],
        [btn("🛍️ Continua a comprare", "show_categories"),
         btn("🏠 Menu", "main_menu")],
    )


# ── Ordini ──

def kb_orders(order_list: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for o in order_list:
        rows.append([btn(
            f"#{o['id']} — {o['date']} — €{o['total']:.2f} {o['status']}",
            f"order:{o['id']}"
        )])
    rows.append([btn("🏠 Menu principale", "main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Ricerca ──

def kb_search_results(results: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for pid in results:
        p = PRODUCTS[pid]
        rows.append([btn(f"{p['emoji']} {p['name']} — €{p['price']:.2f}", f"prod:{pid}")])
    rows.append([btn("🔍 Nuova ricerca", "search_again"),
                 btn("🏠 Menu",          "main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Supporto ──

def kb_support() -> InlineKeyboardMarkup:
    return ikb(
        [btn("💬 Scrivi all'operatore", "support_write")],
        [btn_url("📞 Chiama il negozio", "tel:+390000000000")],
        [btn("🏠 Menu", "main_menu")],
    )


# ═══════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_cart(user_id: int) -> dict[str, int]:
    return carts.get(user_id, {})


def cart_count(user_id: int) -> int:
    return sum(get_cart(user_id).values())


def cart_total(user_id: int, shipping_cost: float = 0.0, discount: float = 0.0) -> float:
    total = sum(
        PRODUCTS[pid]["price"] * qty
        for pid, qty in get_cart(user_id).items()
        if pid in PRODUCTS
    )
    return max(0.0, (total + shipping_cost) * (1 - discount))


def format_product_card(product_id: str) -> str:
    """Genera il testo della scheda prodotto con Markdown HTML."""
    p = PRODUCTS[product_id]
    stars = "★" * int(p["rating"]) + "☆" * (5 - int(p["rating"]))
    badge_line = f"\n🏷️ <b>{p['badge']}</b>" if p.get("badge") else ""
    old_price_line = f"\n<s>€ {p['old_price']:.2f}</s>" if p.get("old_price") else ""
    discount_pct = ""
    if p.get("old_price"):
        pct = int((1 - p["price"] / p["old_price"]) * 100)
        discount_pct = f"  <b>-{pct}%</b>"

    return (
        f"{p['emoji']} <b>{p['name']}</b>{badge_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 {p['description']}\n"
        f"{stars}  ({p['reviews']} recensioni)\n\n"
        f"💰 <b>€ {p['price']:.2f}</b>{discount_pct}{old_price_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 Cosa vuoi fare?"
    )


def format_cart_summary(user_id: int, shipping: Optional[str] = None,
                         coupon: Optional[str] = None) -> tuple[str, float]:
    """Restituisce (testo riepilogo, totale finale)."""
    cart = get_cart(user_id)
    if not cart:
        return "🛒 Il tuo carrello è <b>vuoto</b>.\n\nAggiungi qualcosa dal catalogo!", 0.0

    lines = ["🛒 <b>Il tuo carrello</b>\n━━━━━━━━━━━━━━━━━━━━"]
    subtotal = 0.0
    for pid, qty in cart.items():
        if pid not in PRODUCTS:
            continue
        p = PRODUCTS[pid]
        row_total = p["price"] * qty
        subtotal += row_total
        lines.append(f"{p['emoji']} {p['name']}  ×{qty}  →  <b>€ {row_total:.2f}</b>")

    ship_cost = 0.0
    if shipping and shipping in SHIPPING_OPTIONS:
        emoji, label, ship_cost = SHIPPING_OPTIONS[shipping]
        lines.append(f"\n{emoji} {label}:  € {ship_cost:.2f}")

    discount = 0.0
    if coupon and coupon.upper() in discount_codes:
        discount = discount_codes[coupon.upper()]
        disc_amount = subtotal * discount
        lines.append(f"🏷️ Sconto coupon ({int(discount*100)}%):  <b>−€ {disc_amount:.2f}</b>")

    total = max(0.0, (subtotal + ship_cost) * (1 - discount))
    lines.append(f"━━━━━━━━━━━━━━━━━━━━\n💶 <b>Totale: € {total:.2f}</b>")

    return "\n".join(lines), total


# ═══════════════════════════════════════════════════════════════════
#  ROUTER & HANDLERS
# ═══════════════════════════════════════════════════════════════════

router = Router()


# ── /start ────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    name = user.first_name or "cliente"
    count = cart_count(user.id)

    await message.answer(
        f"👋 Ciao, <b>{name}</b>!\n"
        f"Benvenuto su <b>MioNegozio</b> 🏪\n\n"
        f"Sfoglia il catalogo, aggiungi al carrello e ricevi a casa "
        f"o ritira in negozio.\n\n"
        f"Cosa vuoi fare? 👇",
        reply_markup=reply_main_menu(count),
        parse_mode=ParseMode.HTML,
    )


# ── /menu ─────────────────────────────────────────────────────────

@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    count = cart_count(message.from_user.id)
    await message.answer(
        "🏠 <b>Menu principale</b>\n\nScegli un'opzione qui sotto 👇",
        reply_markup=reply_main_menu(count),
        parse_mode=ParseMode.HTML,
    )


# ── Catalogo ──────────────────────────────────────────────────────

@router.message(F.text == "🛍️ Catalogo")
async def handle_catalogo(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "📂 <b>Scegli una categoria:</b>",
        reply_markup=kb_categories(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "show_categories")
async def cb_show_categories(cq: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cq.message.edit_text(
        "📂 <b>Scegli una categoria:</b>",
        reply_markup=kb_categories(),
        parse_mode=ParseMode.HTML,
    )
    await cq.answer()


@router.callback_query(F.data.startswith("cat:"))
async def cb_category(cq: CallbackQuery, state: FSMContext) -> None:
    category = cq.data.split(":", 1)[1]
    await state.update_data(current_category=category)
    await state.set_state(ShopFSM.browsing_category)

    if category == "offerte":
        products_in_cat = [
            pid for pid, p in PRODUCTS.items() if p.get("badge") in ("SALE", "NEW")
        ]
        title = "🔥 <b>Offerte del giorno</b>"
    else:
        products_in_cat = [
            pid for pid, p in PRODUCTS.items() if p["category"] == category
        ]
        info = CATEGORIES.get(category, ("📦", category.capitalize()))
        title = f"{info[0]} <b>{info[1]}</b>"

    if not products_in_cat:
        await cq.message.edit_text(
            f"{title}\n\n😕 Nessun prodotto disponibile in questa categoria.",
            reply_markup=ikb([btn("◀ Categorie", "show_categories")]),
            parse_mode=ParseMode.HTML,
        )
    else:
        await cq.message.edit_text(
            f"{title}\n\n<i>{len(products_in_cat)} prodotti disponibili</i>",
            reply_markup=kb_product_list(products_in_cat, category),
            parse_mode=ParseMode.HTML,
        )
    await cq.answer()


# ── Scheda prodotto ───────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod:"))
async def cb_product(cq: CallbackQuery, state: FSMContext) -> None:
    product_id = cq.data.split(":", 1)[1]
    if product_id not in PRODUCTS:
        await cq.answer("❌ Prodotto non trovato.", show_alert=True)
        return

    await state.update_data(current_product=product_id)
    await state.set_state(ShopFSM.viewing_product)

    user_id = cq.from_user.id
    is_fav = product_id in favorites.get(user_id, set())

    await cq.message.edit_text(
        format_product_card(product_id),
        reply_markup=kb_product(product_id, is_fav),
        parse_mode=ParseMode.HTML,
    )
    await cq.answer()


@router.callback_query(F.data.startswith("back_cat:"))
async def cb_back_to_category(cq: CallbackQuery, state: FSMContext) -> None:
    product_id = cq.data.split(":", 1)[1]
    category = PRODUCTS.get(product_id, {}).get("category", "abbigliamento")
    # Simula il click sulla categoria
    cq.data = f"cat:{category}"
    await cb_category(cq, state)


@router.callback_query(F.data.startswith("info:"))
async def cb_product_info(cq: CallbackQuery) -> None:
    product_id = cq.data.split(":", 1)[1]
    p = PRODUCTS.get(product_id, {})
    await cq.answer(
        f"ℹ️ {p.get('name','')}\n{p.get('description','')}\n⭐ {p.get('rating',0)}/5 — {p.get('reviews',0)} recensioni",
        show_alert=True,
    )


# ── Aggiungi al carrello ──────────────────────────────────────────

@router.callback_query(F.data.startswith("add:"))
async def cb_add_to_cart(cq: CallbackQuery, state: FSMContext) -> None:
    product_id = cq.data.split(":", 1)[1]
    user_id = cq.from_user.id

    if user_id not in carts:
        carts[user_id] = {}
    carts[user_id][product_id] = carts[user_id].get(product_id, 0) + 1

    count = cart_count(user_id)
    p = PRODUCTS.get(product_id, {})

    # Aggiorna reply keyboard con contatore
    await cq.message.answer(
        f"✅ <b>{p.get('name','Prodotto')}</b> aggiunto al carrello!\n"
        f"🛒 Hai <b>{count}</b> articolo{'i' if count > 1 else ''} nel carrello.",
        reply_markup=reply_main_menu(count),
        parse_mode=ParseMode.HTML,
    )
    await cq.answer("✅ Aggiunto!")


# ── Preferiti ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("fav:"))
async def cb_toggle_favorite(cq: CallbackQuery) -> None:
    product_id = cq.data.split(":", 1)[1]
    user_id = cq.from_user.id

    if user_id not in favorites:
        favorites[user_id] = set()

    if product_id in favorites[user_id]:
        favorites[user_id].discard(product_id)
        await cq.answer("💔 Rimosso dai preferiti")
        is_fav = False
    else:
        favorites[user_id].add(product_id)
        await cq.answer("❤️ Aggiunto ai preferiti!")
        is_fav = True

    await cq.message.edit_reply_markup(
        reply_markup=kb_product(product_id, is_fav)
    )


# ── Carrello ──────────────────────────────────────────────────────

@router.message(F.text.startswith("🛒"))
async def handle_cart(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    cart = get_cart(user_id)
    text, _ = format_cart_summary(user_id)
    await message.answer(
        text,
        reply_markup=kb_cart(has_items=bool(cart)),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "show_cart")
async def cb_show_cart(cq: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    user_id = cq.from_user.id
    cart = get_cart(user_id)
    text, _ = format_cart_summary(
        user_id,
        shipping=data.get("shipping"),
        coupon=data.get("coupon"),
    )
    await cq.message.edit_text(
        text,
        reply_markup=kb_cart(has_items=bool(cart)),
        parse_mode=ParseMode.HTML,
    )
    await cq.answer()


@router.callback_query(F.data == "cart_clear")
async def cb_cart_clear(cq: CallbackQuery, state: FSMContext) -> None:
    user_id = cq.from_user.id
    carts[user_id] = {}
    await state.clear()
    count = 0
    await cq.message.edit_text(
        "🗑️ Carrello svuotato.\n\n🛍️ Torna al catalogo per continuare gli acquisti!",
        reply_markup=ikb([btn("🛍️ Vai al catalogo", "show_categories")]),
        parse_mode=ParseMode.HTML,
    )
    await cq.message.answer(
        "Carrello svuotato.",
        reply_markup=reply_main_menu(count),
    )
    await cq.answer("🗑️ Carrello svuotato")


@router.callback_query(F.data == "cart_coupon")
async def cb_cart_coupon(cq: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ShopFSM.entering_coupon)
    await cq.message.answer(
        "🏷️ <b>Inserisci il codice coupon:</b>\n\n"
        "<i>Es: BENVENUTO10, ESTATE20</i>",
        reply_markup=reply_back_only(),
        parse_mode=ParseMode.HTML,
    )
    await cq.answer()


@router.message(ShopFSM.entering_coupon)
async def handle_coupon_input(message: Message, state: FSMContext) -> None:
    if message.text == "🔙 Menu principale":
        await state.clear()
        await cmd_menu(message, state)
        return

    code = message.text.strip().upper()
    if code in discount_codes:
        disc = int(discount_codes[code] * 100)
        await state.update_data(coupon=code)
        await state.set_state(ShopFSM.cart_review)
        await message.answer(
            f"✅ Coupon <b>{code}</b> applicato! Sconto del <b>{disc}%</b> 🎉",
            reply_markup=reply_main_menu(cart_count(message.from_user.id)),
            parse_mode=ParseMode.HTML,
        )
        # Mostra carrello aggiornato
        user_id = message.from_user.id
        data = await state.get_data()
        text, _ = format_cart_summary(user_id, coupon=code)
        await message.answer(text, reply_markup=kb_cart(), parse_mode=ParseMode.HTML)
    else:
        await message.answer(
            f"❌ Codice <b>{code}</b> non valido o scaduto.\n\n"
            "Riprova o torna al carrello.",
            parse_mode=ParseMode.HTML,
        )


# ── Checkout — Spedizione ─────────────────────────────────────────

@router.callback_query(F.data == "checkout_start")
async def cb_checkout_start(cq: CallbackQuery, state: FSMContext) -> None:
    cart = get_cart(cq.from_user.id)
    if not cart:
        await cq.answer("❌ Il carrello è vuoto!", show_alert=True)
        return
    await state.set_state(ShopFSM.choosing_shipping)
    await cq.message.edit_text(
        "🚚 <b>Come vuoi ricevere il tuo ordine?</b>",
        reply_markup=kb_shipping(),
        parse_mode=ParseMode.HTML,
    )
    await cq.answer()


@router.callback_query(F.data.startswith("ship:"))
async def cb_choose_shipping(cq: CallbackQuery, state: FSMContext) -> None:
    ship_key = cq.data.split(":", 1)[1]
    await state.update_data(shipping=ship_key)

    if ship_key == "home":
        await state.set_state(ShopFSM.entering_address)
        await cq.message.edit_text(
            "📍 <b>Inserisci l'indirizzo di spedizione:</b>\n\n"
            "<i>Es: Via Roma 1, 20100 Milano (MI)</i>",
            reply_markup=ikb([btn("◀ Spedizione", "checkout_start")]),
            parse_mode=ParseMode.HTML,
        )
        await cq.message.answer(
            "Inserisci l'indirizzo 👇",
            reply_markup=reply_back_only(),
        )
    else:
        # Ritiro in negozio → vai diretto al pagamento
        await cb_show_payment(cq, state)
    await cq.answer()


@router.message(ShopFSM.entering_address)
async def handle_address(message: Message, state: FSMContext) -> None:
    if message.text == "🔙 Menu principale":
        await state.clear()
        await cmd_menu(message, state)
        return
    await state.update_data(address=message.text)
    await state.set_state(ShopFSM.choosing_payment)

    data = await state.get_data()
    text, total = format_cart_summary(
        message.from_user.id,
        shipping=data.get("shipping"),
        coupon=data.get("coupon"),
    )
    await message.answer(
        f"📍 Indirizzo salvato: <b>{message.text}</b>\n\n{text}",
        reply_markup=kb_payment(total),
        parse_mode=ParseMode.HTML,
    )


async def cb_show_payment(cq: CallbackQuery, state: FSMContext) -> None:
    """Mostra la schermata pagamento."""
    await state.set_state(ShopFSM.choosing_payment)
    data = await state.get_data()
    _, total = format_cart_summary(
        cq.from_user.id,
        shipping=data.get("shipping"),
        coupon=data.get("coupon"),
    )
    await cq.message.edit_text(
        "💳 <b>Scegli il metodo di pagamento:</b>",
        reply_markup=kb_payment(total),
        parse_mode=ParseMode.HTML,
    )


# ── Checkout — Pagamento ──────────────────────────────────────────

@router.callback_query(F.data.startswith("pay:"))
async def cb_payment(cq: CallbackQuery, state: FSMContext) -> None:
    method = cq.data.split(":", 1)[1]
    data = await state.get_data()
    user_id = cq.from_user.id

    _, total = format_cart_summary(
        user_id,
        shipping=data.get("shipping"),
        coupon=data.get("coupon"),
    )

    # Genera ID ordine mock
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Svuota carrello dopo l'ordine
    carts[user_id] = {}
    await state.clear()

    method_labels = {"card": "💳 Carta", "bank": "🏦 Bonifico", "paypal": "💸 PayPal"}
    pay_label = method_labels.get(method, "💳 Pagamento")

    await cq.message.edit_text(
        f"✅ <b>Ordine confermato!</b>\n\n"
        f"📋 Numero ordine: <code>{order_id}</code>\n"
        f"💶 Totale pagato: <b>€ {total:.2f}</b>\n"
        f"💳 Metodo: {pay_label}\n\n"
        f"Riceverai una notifica quando il pacco sarà spedito 📦\n"
        f"Grazie per aver acquistato da <b>MioNegozio</b>! 🙏",
        reply_markup=kb_order_confirmed(order_id),
        parse_mode=ParseMode.HTML,
    )
    await cq.message.answer(
        "🎉 Grazie per il tuo ordine!",
        reply_markup=reply_main_menu(0),
    )
    await cq.answer("✅ Ordine confermato!")


# ── Ricerca ───────────────────────────────────────────────────────

@router.message(F.text == "🔍 Cerca")
async def handle_search(message: Message, state: FSMContext) -> None:
    await state.set_state(ShopFSM.searching)
    await message.answer(
        "🔍 <b>Cerca nel catalogo:</b>\n\n"
        "Digita il nome del prodotto o una parola chiave.",
        reply_markup=reply_back_only(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "search_again")
async def cb_search_again(cq: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ShopFSM.searching)
    await cq.message.answer(
        "🔍 Digita una nuova ricerca:",
        reply_markup=reply_back_only(),
    )
    await cq.answer()


@router.message(ShopFSM.searching)
async def handle_search_input(message: Message, state: FSMContext) -> None:
    if message.text == "🔙 Menu principale":
        await state.clear()
        await cmd_menu(message, state)
        return

    query = message.text.strip().lower()
    results = [
        pid for pid, p in PRODUCTS.items()
        if query in p["name"].lower() or query in p["description"].lower()
           or query in p["category"]
    ]

    if not results:
        await message.answer(
            f"😕 Nessun risultato per <b>"{query}"</b>.\n\nProva con un'altra parola chiave.",
            reply_markup=ikb(
                [btn("🛍️ Vai al catalogo", "show_categories")],
                [btn("🏠 Menu", "main_menu")],
            ),
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.answer(
            f"🔍 <b>Risultati per "{query}":</b>  {len(results)} trovati",
            reply_markup=kb_search_results(results),
            parse_mode=ParseMode.HTML,
        )
    await state.clear()


# ── Ordini ────────────────────────────────────────────────────────

@router.message(F.text == "📦 I miei ordini")
async def handle_orders(message: Message, state: FSMContext) -> None:
    await state.clear()
    # Dati mock — collegare a DB reale
    mock_orders = [
        {"id": "ORD20240610", "date": "10/06/2024", "total": 27.31, "status": "✅"},
        {"id": "ORD20240520", "date": "20/05/2024", "total": 89.00, "status": "📦"},
    ]
    await message.answer(
        "📦 <b>I tuoi ordini:</b>",
        reply_markup=kb_orders(mock_orders),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data.startswith("order:"))
async def cb_order_detail(cq: CallbackQuery) -> None:
    order_id = cq.data.split(":", 1)[1]
    await cq.message.edit_text(
        f"📋 <b>Ordine {order_id}</b>\n\n"
        f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}\n"
        f"📦 Stato: In consegna\n"
        f"🚚 Tracking: disponibile a breve\n\n"
        f"<i>Riceverai un SMS con il link di tracciamento.</i>",
        reply_markup=ikb(
            [btn("📦 Traccia spedizione", f"track:{order_id}")],
            [btn("◀ I miei ordini", "orders_list"),
             btn("🏠 Menu", "main_menu")],
        ),
        parse_mode=ParseMode.HTML,
    )
    await cq.answer()


@router.callback_query(F.data.startswith("track:"))
async def cb_track(cq: CallbackQuery) -> None:
    await cq.answer("🚚 Tracking disponibile tra 24h dalla spedizione.", show_alert=True)


# ── Preferiti ─────────────────────────────────────────────────────

@router.message(F.text == "❤️ Preferiti")
async def handle_favorites(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    favs = favorites.get(user_id, set())

    if not favs:
        await message.answer(
            "❤️ <b>Preferiti</b>\n\n"
            "Non hai ancora salvato nessun prodotto.\n"
            "Sfoglia il catalogo e premi 🤍 su ciò che ti piace!",
            reply_markup=ikb([btn("🛍️ Vai al catalogo", "show_categories")]),
            parse_mode=ParseMode.HTML,
        )
    else:
        fav_list = [pid for pid in favs if pid in PRODUCTS]
        await message.answer(
            f"❤️ <b>Preferiti</b>  ({len(fav_list)} prodotti salvati)",
            reply_markup=kb_product_list(fav_list, "preferiti"),
            parse_mode=ParseMode.HTML,
        )


# ── Profilo ───────────────────────────────────────────────────────

@router.message(F.text == "👤 Profilo")
async def handle_profile(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    await message.answer(
        f"👤 <b>Il tuo profilo</b>\n\n"
        f"📛 Nome: <b>{user.full_name}</b>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🌐 Username: @{user.username or '—'}\n\n"
        f"🛒 Articoli nel carrello: <b>{cart_count(user.id)}</b>\n"
        f"❤️ Preferiti: <b>{len(favorites.get(user.id, set()))}</b>",
        reply_markup=ikb(
            [btn("📋 I miei ordini", "orders_list")],
            [btn("❤️ Preferiti",     "fav_list")],
            [btn("🏠 Menu",          "main_menu")],
        ),
        parse_mode=ParseMode.HTML,
    )


# ── Info Negozio ──────────────────────────────────────────────────

@router.message(F.text == "📍 Negozio")
async def handle_store(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "📍 <b>MioNegozio</b>\n\n"
        "🏪 Via Roma 1, 20100 Milano (MI)\n"
        "📞 +39 02 0000000\n"
        "✉️ info@mionegozio.it\n\n"
        "🕐 <b>Orari:</b>\n"
        "Lun–Ven: 9:00 – 19:00\n"
        "Sab: 9:00 – 13:00\n"
        "Dom: chiuso\n\n"
        "🚇 <i>MM1 – Stazione Centrale</i>",
        reply_markup=ikb(
            [btn_url("🗺️ Apri su Google Maps", "https://maps.google.com")],
            [btn("🏠 Menu", "main_menu")],
        ),
        parse_mode=ParseMode.HTML,
    )


# ── Supporto ─────────────────────────────────────────────────────

@router.message(F.text == "🎧 Supporto")
async def handle_support(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🎧 <b>Supporto clienti</b>\n\n"
        "Siamo qui per aiutarti!\n"
        "Tempo medio di risposta: <b>< 2 ore</b> 🕐",
        reply_markup=kb_support(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "support_write")
async def cb_support_write(cq: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ShopFSM.support_message)
    await cq.message.answer(
        "💬 <b>Scrivi il tuo messaggio:</b>\n\n"
        "Descrivi il tuo problema e ti risponderemo al più presto.",
        reply_markup=reply_back_only(),
        parse_mode=ParseMode.HTML,
    )
    await cq.answer()


@router.message(ShopFSM.support_message)
async def handle_support_message(message: Message, state: FSMContext) -> None:
    if message.text == "🔙 Menu principale":
        await state.clear()
        await cmd_menu(message, state)
        return

    await state.clear()
    await message.answer(
        "✅ <b>Messaggio inviato!</b>\n\n"
        "Il nostro team ti risponderà entro 2 ore lavorative.\n"
        "Grazie per la pazienza 🙏",
        reply_markup=reply_main_menu(cart_count(message.from_user.id)),
        parse_mode=ParseMode.HTML,
    )
    # In produzione: inoltro messaggio al gruppo admin
    logger.info(f"[SUPPORT] User {message.from_user.id}: {message.text}")


# ── Callback generici ─────────────────────────────────────────────

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(cq: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    count = cart_count(cq.from_user.id)
    await cq.message.edit_text(
        "🏠 <b>Menu principale</b>",
        reply_markup=None,
        parse_mode=ParseMode.HTML,
    )
    await cq.message.answer(
        "Scegli un'opzione 👇",
        reply_markup=reply_main_menu(count),
    )
    await cq.answer()


@router.message(F.text == "🔙 Menu principale")
async def handle_back_to_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await cmd_menu(message, state)


# ── Catch-all ────────────────────────────────────────────────────

@router.message()
async def handle_unknown(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state:
        return  # Lasciar gestire agli handler FSM attivi
    count = cart_count(message.from_user.id)
    await message.answer(
        "🤔 Non ho capito. Usa i pulsanti qui sotto oppure digita /menu.",
        reply_markup=reply_main_menu(count),
    )


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logger.info("🚀 MioNegozio Bot avviato — in ascolto...")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
