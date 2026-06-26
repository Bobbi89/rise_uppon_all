# ═══════════════════════════════════════════════════════════════════
#  Oro Naturale — Keyboards  (V3 — allineato ideogramma)
#  Tutte le tastiere inline e reply del bot
# ═══════════════════════════════════════════════════════════════════
#
#  MAPPA SCHERMATE V3
#  ┌─────────────────────────────────────────────────────────────┐
#  │  UTENTE                                                     │
#  │  01 Home           → welcome_menu()  +  main_menu()        │
#  │  02 Catalogo       → categories_menu()  product_list_menu()│
#  │                      product_card_menu()                    │
#  │  03 Checkout       → cart_menu()  shipping_menu()          │
#  │                      payment_menu()  order_confirmed_menu() │
#  │  04 I miei ordini  → orders_menu()  order_detail_menu()    │
#  │  05 Post-vendita   → tracking_menu()  review_menu()        │
#  ├─────────────────────────────────────────────────────────────┤
#  │  ADMIN (solo admin_id)                                      │
#  │  06 Dashboard      → admin_dashboard_menu()                │
#  │  07 Gestione ord.  → admin_orders_menu()                   │
#  │                      admin_order_actions_menu()             │
#  │  08 Alert ordine   → admin_new_order_menu()                │
#  └─────────────────────────────────────────────────────────────┘
#
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


# ═══════════════════════════════════════════════════════════════════
#  COSTANTI CATEGORIE
# ═══════════════════════════════════════════════════════════════════

CATEGORY_META: dict[str, dict[str, str]] = {
    "extra_virgin_olive_oil": {
        "emoji": "🌿",
        "label": "Oli Extravergine",
    },
    "flavored_oil": {
        "emoji": "🧃",
        "label": "Oli Aromatizzati",
    },
    "wine": {
        "emoji": "🍷",
        "label": "Vini",
    },
    "cosmetics": {
        "emoji": "🧴",
        "label": "Cosmetica",
    },
    "gift_box": {
        "emoji": "🎁",
        "label": "Gift Box",
    },
}

# Emoji stato ordine — usata in testo e admin
ORDER_STATUS_EMOJI: dict[str, str] = {
    "pending":   "⏳ In attesa",
    "confirmed": "✅ Confermato",
    "shipped":   "🚚 Spedito",
    "delivered": "📦 Consegnato",
    "cancelled": "❌ Annullato",
}


# ═══════════════════════════════════════════════════════════════════
#  HELPER INTERNI
# ═══════════════════════════════════════════════════════════════════

def _ikb(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    """Costruisce InlineKeyboardMarkup da righe di bottoni."""
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


def _btn(text: str, data: str) -> InlineKeyboardButton:
    """Bottone callback."""
    return InlineKeyboardButton(text=text, callback_data=data)


def _btn_url(text: str, url: str) -> InlineKeyboardButton:
    """Bottone URL esterno."""
    return InlineKeyboardButton(text=text, url=url)


# ═══════════════════════════════════════════════════════════════════
#  SCREEN 01 — HOME
#  Reply keyboard persistente + inline welcome
# ═══════════════════════════════════════════════════════════════════

def main_menu(cart_count: int = 0) -> ReplyKeyboardMarkup:
    """
    Reply keyboard fissa — visibile sempre in basso.
    Corrisponde ai pulsanti veloci del menu principale (screen 01).

    Layout V3:
        [ 🛍️ Catalogo ]  [ 🔍 Cerca      ]
        [ 🛒 Carrello  ]  [ 📦 Miei ordini ]
        [ ❤️ Preferiti ]  [ 👤 Profilo     ]
        [ 📍 Negozio   ]  [ 🎧 Supporto    ]
    """
    cart_label = (
        f"🛒 Carrello ({cart_count})" if cart_count > 0 else "🛒 Carrello"
    )
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🛍️ Catalogo"),
                KeyboardButton(text="🔍 Cerca"),
            ],
            [
                KeyboardButton(text=cart_label),
                KeyboardButton(text="📦 I miei ordini"),
            ],
            [
                KeyboardButton(text="❤️ Preferiti"),
                KeyboardButton(text="👤 Profilo"),
            ],
            [
                KeyboardButton(text="📍 Negozio"),
                KeyboardButton(text="🎧 Supporto"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def welcome_menu() -> InlineKeyboardMarkup:
    """
    Inline keyboard nel messaggio di benvenuto (screen 01).
    Bottone principale → catalogo; secondari → ordini e info.
    """
    return _ikb(
        [_btn("🛍️ Apri Catalogo Prodotti", "show_categories")],
        [
            _btn("📦 I Miei Ordini", "orders_list"),
            _btn("⭐ Preferiti",    "fav_list"),
        ],
        [
            _btn("💬 Assistenza", "support"),
            _btn("ℹ️ Spedizioni", "info_shipping"),
        ],
    )


def back_only() -> ReplyKeyboardMarkup:
    """Mini keyboard con solo torna al menu."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Menu principale")]],
        resize_keyboard=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  SCREEN 02 — CATALOGO
#  Categorie → Lista prodotti → Scheda prodotto
# ═══════════════════════════════════════════════════════════════════

def categories_menu(
    featured_ids: list[str] | None = None,
) -> InlineKeyboardMarkup:
    """
    Griglia categorie 2 colonne (screen 02).
    Aggiunge riga "In evidenza" se ci sono prodotti featured.
    """
    rows: list[list[InlineKeyboardButton]] = []
    cats = list(CATEGORY_META.items())

    for i in range(0, len(cats), 2):
        row: list[InlineKeyboardButton] = []
        for key, meta in cats[i : i + 2]:
            row.append(_btn(f"{meta['emoji']} {meta['label']}", f"cat:{key}"))
        rows.append(row)

    if featured_ids:
        rows.append([_btn("⭐ In evidenza", "cat:featured")])

    rows.append([_btn("🏠 Menu", "main_menu")])
    return _ikb(*rows)


def product_list_menu(
    products: list[dict],
    category: str,
    page: int = 0,
    per_page: int = 10,
) -> InlineKeyboardMarkup:
    """
    Lista prodotti con paginazione (screen 02).
    Una riga per prodotto; nav ◀ ▶ se ci sono più pagine.
    """
    rows: list[list[InlineKeyboardButton]] = []

    start = page * per_page
    page_items = products[start : start + per_page]

    for p in page_items:
        pid   = p.get("id", "")
        name  = p.get("name", "Prodotto")
        price = p.get("price", 0.0)
        stock = int(p.get("stock", 0))

        prefix  = "⛔ " if stock <= 0 else ""
        starred = " ⭐" if p.get("featured") in (True, "true") else ""
        label   = f"{prefix}{name} — €{float(price):.2f}{starred}"
        rows.append([_btn(label, f"prod:{pid}")])

    # Navigazione pagine
    total_pages = max(1, (len(products) + per_page - 1) // per_page)
    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(_btn("◀ Precedente", f"cat_page:{category}:{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(_btn("Successiva ▶", f"cat_page:{category}:{page + 1}"))
    if nav_row:
        rows.append(nav_row)

    rows.append([
        _btn("◀ Categorie", "show_categories"),
        _btn("🏠 Menu",     "main_menu"),
    ])
    return _ikb(*rows)


def product_card_menu(
    product_id: str,
    category: str,
    stock: int,
    is_fav: bool = False,
) -> InlineKeyboardMarkup:
    """
    Scheda prodotto (screen 02).

    Layout V3:
        [ 🛒 Aggiungi al carrello ]   ← solo se disponibile
        [ ❤️/🤍 Preferiti ]  [ ℹ️ Dettagli ]
        [ ◀ Categoria      ]  [ 🏠 Menu     ]
    """
    rows: list[list[InlineKeyboardButton]] = []

    if stock > 0:
        rows.append([_btn("🛒 Aggiungi al carrello", f"add:{product_id}")])
    else:
        rows.append([_btn("⛔ Esaurito", "noop")])

    fav_label = "❤️ Salvato" if is_fav else "🤍 Salva"
    rows.append([
        _btn(fav_label,     f"fav:{product_id}"),
        _btn("ℹ️ Dettagli", f"info:{product_id}"),
    ])
    rows.append([
        _btn("◀ Torna alla categoria", f"back_cat:{category}"),
        _btn("🏠 Menu",                "main_menu"),
    ])
    return _ikb(*rows)


def quantity_menu(
    product_id: str,
    current_qty: int,
    max_qty: int,
) -> InlineKeyboardMarkup:
    """Selettore quantità inline (− qty +)."""
    qty_row: list[InlineKeyboardButton] = []

    if current_qty > 1:
        qty_row.append(_btn("➖ Meno",  f"qty:{product_id}:{current_qty - 1}"))
    else:
        qty_row.append(_btn("🗑️ Rimuovi", f"qty:{product_id}:0"))

    piece = "pezzo" if current_qty == 1 else "pezzi"
    qty_row.append(_btn(f"📏 {current_qty} {piece}", "noop"))

    if current_qty < max_qty:
        qty_row.append(_btn("➕ Più", f"qty:{product_id}:{current_qty + 1}"))
    else:
        qty_row.append(_btn("🚫 Max", "noop"))

    return _ikb(qty_row, [_btn("◀ Torna al carrello", "show_cart")])


# ═══════════════════════════════════════════════════════════════════
#  SCREEN 03 — CHECKOUT
#  Carrello → Spedizione → Pagamento → Conferma
# ═══════════════════════════════════════════════════════════════════

def cart_menu(has_items: bool = True) -> InlineKeyboardMarkup:
    """
    Vista carrello (screen 03).

    Se vuoto → solo CTA verso catalogo.
    Se pieno → checkout, modifica, coupon, svuota.
    """
    if not has_items:
        return _ikb(
            [_btn("🛍️ Vai al catalogo", "show_categories")],
        )
    return _ikb(
        [_btn("✅ Procedi al checkout", "checkout_start")],
        [
            _btn("✏️ Modifica quantità", "cart_edit"),
            _btn("🏷️ Inserisci coupon",  "cart_coupon"),
        ],
        [
            _btn("🗑️ Svuota carrello",   "cart_clear"),
            _btn("🛍️ Continua acquisti", "show_categories"),
        ],
    )


def shipping_menu() -> InlineKeyboardMarkup:
    """
    Scelta metodo di spedizione (screen 03).

    Layout V3:
        [ 📦 Spedizione a casa  (+€4,90) ]
        [ 🏪 Ritiro in negozio (gratuito) ]
        [ ◀ Torna al carrello            ]
    """
    return _ikb(
        [_btn("📦 Spedizione a casa  (+€4,90)",    "ship:home")],
        [_btn("🏪 Ritiro in negozio (gratuito)",   "ship:pickup")],
        [_btn("◀ Torna al carrello",               "show_cart")],
    )


def payment_menu(total: float) -> InlineKeyboardMarkup:
    """
    Scelta metodo di pagamento (screen 03).
    Bonifico rimosso — V3 prevede solo Carta e PayPal.

    Layout V3:
        [ 💳 Paga con Carta ]
        [ 💸 Paga con PayPal ]
        [ ◀ Modifica spedizione ]
    """
    return _ikb(
        [_btn(f"💳 Paga con Carta — €{total:.2f}",  "pay:card")],
        [_btn(f"💸 Paga con PayPal — €{total:.2f}", "pay:paypal")],
        [_btn("◀ Modifica spedizione",              "checkout_start")],
    )


def order_confirmed_menu(order_id: str) -> InlineKeyboardMarkup:
    """
    Messaggio post-pagamento (screen 03 → transizione screen 04).

    Layout V3:
        [ 🔗 Traccia spedizione ]
        [ 🛍️ Continua acquisti ]  [ 🏠 Menu ]
    """
    return _ikb(
        [_btn("🔗 Traccia spedizione",    f"track:{order_id}")],
        [
            _btn("🛍️ Continua acquisti", "show_categories"),
            _btn("🏠 Menu",              "main_menu"),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
#  SCREEN 04 — I MIEI ORDINI
#  Storico + dettaglio singolo ordine
# ═══════════════════════════════════════════════════════════════════

def orders_menu(order_list: list[dict]) -> InlineKeyboardMarkup:
    """
    Lista ordini dell'utente (screen 04).

    Ogni riga mostra: #ID — data — €totale — emoji stato
    Il testo dello stato proviene da ORDER_STATUS_EMOJI.
    """
    rows: list[list[InlineKeyboardButton]] = []
    for o in order_list:
        status_label = ORDER_STATUS_EMOJI.get(o.get("status", ""), o.get("status", ""))
        label = (
            f"#{o['id']} · {o['date']} · €{float(o['total']):.2f}  {status_label}"
        )
        rows.append([_btn(label, f"order:{o['id']}")])

    rows.append([_btn("🏠 Menu principale", "main_menu")])
    return _ikb(*rows)


def order_detail_menu(order_id: str) -> InlineKeyboardMarkup:
    """
    Dettaglio ordine (screen 04 → screen 05).

    Layout V3:
        [ 🔗 Traccia spedizione ]
        [ ◀ I miei ordini ]  [ 🏠 Menu ]
    """
    return _ikb(
        [_btn("🔗 Traccia spedizione", f"track:{order_id}")],
        [
            _btn("◀ I miei ordini", "orders_list"),
            _btn("🏠 Menu",         "main_menu"),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
#  SCREEN 05 — POST-VENDITA
#  Tracking spedizione + richiesta recensione automatica
# ═══════════════════════════════════════════════════════════════════

def tracking_menu(order_id: str, tracking_url: str | None = None) -> InlineKeyboardMarkup:
    """
    Schermata tracking (screen 05 — stato "Spedito").

    Se disponibile, aggiunge bottone URL diretto al corriere.
    Layout V3:
        [ 🔗 Traccia Pacco ]   ← URL esterno se tracking_url, altrimenti callback
        [ 🎧 Assistenza ]  [ ◀ Ordini ]
    """
    rows: list[list[InlineKeyboardButton]] = []

    if tracking_url:
        rows.append([_btn_url("🔗 Traccia Pacco", tracking_url)])
    else:
        rows.append([_btn("🔗 Traccia Pacco", f"track:{order_id}")])

    rows.append([
        _btn("🎧 Assistenza", "support"),
        _btn("◀ Ordini",     "orders_list"),
    ])
    return _ikb(*rows)


def review_menu(order_id: str) -> InlineKeyboardMarkup:
    """
    Richiesta recensione automatica post-consegna (screen 05).

    Layout V3:
        [ ⭐1 ] [ ⭐2 ] [ ⭐3 ] [ ⭐4 ] [ ⭐5 ]
        [ ⏭️ Non ora ]
    """
    return _ikb(
        [
            _btn("⭐ 1", f"review:{order_id}:1"),
            _btn("⭐ 2", f"review:{order_id}:2"),
            _btn("⭐ 3", f"review:{order_id}:3"),
            _btn("⭐ 4", f"review:{order_id}:4"),
            _btn("⭐ 5", f"review:{order_id}:5"),
        ],
        [_btn("⏭️ Non ora", f"review:{order_id}:skip")],
    )


# ═══════════════════════════════════════════════════════════════════
#  SCREEN 06 — ADMIN DASHBOARD
#  Comando /admin — solo utenti in ADMIN_IDS
# ═══════════════════════════════════════════════════════════════════

def admin_dashboard_menu(pending_count: int = 0) -> InlineKeyboardMarkup:
    """
    Dashboard admin (screen 06).

    pending_count viene mostrato sul badge "Gestisci Ordini".
    Layout V3:
        [ 📦 Gestisci Ordini (N) ]
        [ ➕ Nuovo Prodotto ]  [ ✏️ Catalogo    ]
        [ 📊 Statistiche   ]  [ ⚙️ Impostazioni ]
    """
    order_label = (
        f"📦 Gestisci Ordini ({pending_count})"
        if pending_count > 0
        else "📦 Gestisci Ordini"
    )
    return _ikb(
        [_btn(order_label,           "admin_orders")],
        [
            _btn("➕ Nuovo Prodotto", "admin_product_new"),
            _btn("✏️ Catalogo",       "admin_catalog"),
        ],
        [
            _btn("📊 Statistiche",    "admin_stats"),
            _btn("⚙️ Impostazioni",   "admin_settings"),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
#  SCREEN 07 — ADMIN GESTIONE ORDINI
# ═══════════════════════════════════════════════════════════════════

def admin_orders_menu(order_list: list[dict]) -> InlineKeyboardMarkup:
    """
    Lista ordini pendenti lato admin (screen 07).

    Ogni riga: #ID · cliente · €totale · stato
    """
    rows: list[list[InlineKeyboardButton]] = []
    for o in order_list:
        status_label = ORDER_STATUS_EMOJI.get(o.get("status", ""), o.get("status", ""))
        label = (
            f"#{o['id']} · {o.get('customer_name', 'N/D')} · "
            f"€{float(o.get('total', 0)):.2f}  {status_label}"
        )
        rows.append([_btn(label, f"admin_order:{o['id']}")])

    rows.append([_btn("◀ Dashboard", "admin_dashboard")])
    return _ikb(*rows)


def admin_order_actions_menu(order_id: str) -> InlineKeyboardMarkup:
    """
    Azioni su singolo ordine admin (screen 07 — dettaglio).

    Layout V3:
        [ 🚚 Segna come SPEDITO ]
        [ 💬 Contatta Utente ]  [ ⚠️ Annulla ]
        [ ◀ Ordini Admin     ]
    """
    return _ikb(
        [_btn("🚚 Segna come SPEDITO",  f"admin_ship:{order_id}")],
        [
            _btn("💬 Contatta Utente",  f"admin_contact:{order_id}"),
            _btn("⚠️ Annulla Ordine",   f"admin_cancel:{order_id}"),
        ],
        [_btn("◀ Ordini Admin", "admin_orders")],
    )


# ═══════════════════════════════════════════════════════════════════
#  SCREEN 08 — ADMIN ALERT NUOVO ORDINE
#  Inviato automaticamente al canale/chat admin ad ogni ordine
# ═══════════════════════════════════════════════════════════════════

def admin_new_order_menu(order_id: str) -> InlineKeyboardMarkup:
    """
    Alert notifica nuovo ordine (screen 08).
    Inviato al canale admin privato appena Stripe conferma il pagamento.

    Layout V3:
        [ 🚚 Segna come SPEDITO ]
        [ 💬 Contatta Utente ]  [ ⚠️ Annulla ]
    """
    return _ikb(
        [_btn("🚚 Segna come SPEDITO", f"admin_ship:{order_id}")],
        [
            _btn("💬 Contatta Utente", f"admin_contact:{order_id}"),
            _btn("⚠️ Annulla Ordine",  f"admin_cancel:{order_id}"),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
#  KEYBOARDS ACCESSORIE
# ═══════════════════════════════════════════════════════════════════

def search_results_menu(results: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for p in results:
        pid   = p.get("id", "")
        name  = p.get("name", "Prodotto")
        price = p.get("price", 0.0)
        rows.append([_btn(f"{name} — €{float(price):.2f}", f"prod:{pid}")])
    rows.append([
        _btn("🔍 Nuova ricerca", "search_again"),
        _btn("🏠 Menu",          "main_menu"),
    ])
    return _ikb(*rows)


def search_no_results_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("🛍️ Vai al catalogo", "show_categories")],
        [_btn("🏠 Menu",            "main_menu")],
    )


def favorites_menu(products: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for p in products:
        pid   = p.get("id", "")
        name  = p.get("name", "Prodotto")
        price = p.get("price", 0.0)
        rows.append([_btn(f"{name} — €{float(price):.2f}", f"prod:{pid}")])
    rows.append([_btn("🛍️ Vai al catalogo", "show_categories")])
    return _ikb(*rows)


def favorites_empty_menu() -> InlineKeyboardMarkup:
    return _ikb([_btn("🛍️ Vai al catalogo", "show_categories")])


def profile_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("📋 I miei ordini", "orders_list")],
        [_btn("❤️ Preferiti",     "fav_list")],
        [_btn("🏠 Menu",          "main_menu")],
    )


def store_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn_url("🗺️ Apri su Google Maps", "https://maps.google.com")],
        [_btn("🏠 Menu", "main_menu")],
    )


def support_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("💬 Scrivi all'operatore",         "support_write")],
        [_btn_url("📞 Chiama il negozio",        "tel:+390000000000")],
        [_btn("🏠 Menu",                         "main_menu")],
    )


def back_to_categories_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("◀ Categorie", "show_categories")],
        [_btn("🏠 Menu",     "main_menu")],
    )


def back_to_cart_menu() -> InlineKeyboardMarkup:
    return _ikb([_btn("◀ Torna al carrello", "show_cart")])


def back_to_shipping_menu() -> InlineKeyboardMarkup:
    return _ikb([_btn("◀ Modifica spedizione", "checkout_start")])


# ═══════════════════════════════════════════════════════════════════
#  FORMATTERS — Testo messaggi
# ═══════════════════════════════════════════════════════════════════

def format_product_card(p: dict) -> str:
    """Genera il testo della scheda prodotto (screen 02)."""
    name        = p.get("name", "Prodotto")
    description = p.get("description", "")
    price       = p.get("price", 0.0)
    stock       = int(p.get("stock", 0))
    category    = p.get("category", "")
    details     = p.get("details", {})
    is_featured = p.get("featured") in (True, "true")

    badge_line = "\n⭐ <b>In evidenza</b>" if is_featured else ""

    if stock <= 0:
        stock_line = "\n⛔ <b>Esaurito</b>"
    elif stock <= 5:
        stock_line = f"\n⚠️ Solo {stock} rimast{'o' if stock == 1 else 'i'}!"
    else:
        stock_line = f"\n✅ Disponibile ({stock} pezzi)"

    detail_lines: list[str] = []
    if isinstance(details, dict):
        if origin := details.get("origin"):
            detail_lines.append(f"📍 Origine: {origin}")
        if volume := details.get("volume"):
            detail_lines.append(f"📦 Formato: {volume}")
        if harvest := details.get("harvest_year"):
            detail_lines.append(f"🌾 Raccolto: {harvest}")
        if chars := details.get("characteristics"):
            if isinstance(chars, list) and chars:
                detail_lines.append(f"🎯 {' · '.join(chars)}")

    cat_meta  = CATEGORY_META.get(category, {})
    cat_emoji = cat_meta.get("emoji", "📦")
    cat_label = cat_meta.get("label", category.replace("_", " ").title())

    sep = "━" * 20
    text = (
        f"{cat_emoji} <b>{name}</b>{badge_line}\n"
        f"{sep}\n"
        f"{description}\n"
    )
    if detail_lines:
        text += "\n" + "\n".join(detail_lines) + "\n"
    text += (
        f"{stock_line}\n"
        f"{sep}\n"
        f"💰 <b>€ {float(price):.2f}</b>\n"
        f"{sep}\n"
        f"👇 Cosa vuoi fare?"
    )
    return text


def format_cart_summary(
    cart_items: list[dict],
    products_map: dict[str, dict],
    shipping: str | None = None,
    shipping_cost: float = 0.0,
    coupon: str | None = None,
    discount: float = 0.0,
) -> tuple[str, float]:
    """
    Restituisce (testo riepilogo carrello, totale finale).
    Usato in screen 03 — Checkout.
    """
    sep = "━" * 20

    if not cart_items:
        return (
            "🛒 Il tuo carrello è <b>vuoto</b>.\n\n"
            "Aggiungi qualcosa dal catalogo!",
            0.0,
        )

    lines: list[str] = [f"🛒 <b>Il tuo carrello</b>\n{sep}"]
    subtotal       = 0.0
    total_pieces   = 0

    for item in cart_items:
        pid = item.get("product_id", "")
        qty = item.get("qty", 0)
        p   = products_map.get(pid)
        if not p:
            continue
        name      = p.get("name", "Prodotto")
        price     = float(p.get("price", 0.0))
        row_total = price * qty
        subtotal += row_total
        total_pieces += qty
        lines.append(f"🌿 {name}  x{qty}  →  <b>€ {row_total:.2f}</b>")

    # Spedizione
    if shipping == "home":
        lines.append(f"\n📦 Spedizione a casa:  € {shipping_cost:.2f}")
    elif shipping == "pickup":
        lines.append("\n🏪 Ritiro in negozio:  <b>Gratuito</b>")

    # Coupon
    if coupon and discount > 0:
        disc_amount = subtotal * discount
        disc_pct    = int(discount * 100)
        lines.append(f"🏷️ Sconto coupon ({disc_pct}%):  <b>− € {disc_amount:.2f}</b>")

    total = max(0.0, (subtotal + shipping_cost) * (1 - discount))
    piece_label = "articolo" if total_pieces == 1 else "articoli"
    lines += [
        sep,
        f"💴 <b>Totale: € {total:.2f}</b>  ({total_pieces} {piece_label})",
    ]
    return "\n".join(lines), total


def format_order_confirmed(
    order_id: str,
    total: float,
    method_label: str,
    shipping_label: str,
    address: str | None = None,
) -> str:
    """Messaggio conferma ordine (fine screen 03)."""
    text = (
        f"✅ <b>Ordine confermato!</b>\n\n"
        f"📋 Numero: <code>{order_id}</code>\n"
        f"💴 Totale: <b>€ {total:.2f}</b>\n"
        f"💳 Metodo: {method_label}\n"
        f"🛢️ Spedizione: {shipping_label}\n"
    )
    if address:
        text += f"📍 Indirizzo: <b>{address}</b>\n"
    text += (
        f"\nRiceverai una notifica quando il pacco sarà spedito 📦\n"
        f"Grazie per aver acquistato da <b>Oro Naturale</b>! 🙏"
    )
    return text


def format_orders_header(count: int) -> str:
    """Header lista ordini utente (screen 04)."""
    if count == 0:
        return (
            "📦 <b>I tuoi ordini</b>\n\n"
            "Non hai ancora effettuato ordini.\n"
            "Sfoglia il catalogo e fai il tuo primo acquisto!"
        )
    return f"📦 <b>I tuoi ordini recenti</b>  ({count} ordini)"


def format_order_detail(order: dict) -> str:
    """
    Testo dettaglio ordine utente (screen 04 → screen 05).
    Mostra stato con emoji, indirizzo, prodotti e tracking note.
    """
    order_id = order.get("id", "")
    date     = order.get("date", "")
    status   = order.get("status", "")
    total    = float(order.get("total", 0.0))
    items    = order.get("items", "")
    address  = order.get("address", "")

    status_label = ORDER_STATUS_EMOJI.get(status, status)
    sep = "━" * 20

    text = (
        f"🔍 <b>DETTAGLIO ORDINE #{order_id}</b>\n\n"
        f"📅 Data: {date}\n"
    )
    if items:
        text += f"\n🛍 <b>Articoli:</b>\n{items}\n"
    if address:
        text += f"\n📍 <b>Spedito a:</b>\n{address}\n"
    text += (
        f"\n🚚 <b>STATO: {status_label}</b>\n"
        f"{sep}\n"
        f"💴 <b>Totale: € {total:.2f}</b>\n\n"
        f"<i>Riceverai un SMS con il link di tracciamento.</i>"
    )
    return text


def format_tracking_message(order_id: str, status: str, carrier_note: str = "") -> str:
    """
    Testo messaggio tracking (screen 05 — stato Spedito).
    carrier_note: es. "GLS · TN123456789IT"
    """
    status_label = ORDER_STATUS_EMOJI.get(status, status)
    text = (
        f"📦 <b>Tracking Ordine #{order_id}</b>\n\n"
        f"🚚 <b>STATO: {status_label}</b> 🟢\n"
    )
    if carrier_note:
        text += f"\n{carrier_note}\n"
    text += "\nIl tuo pacco è in viaggio verso di te!"
    return text


def format_review_request(order_id: str) -> str:
    """Testo richiesta recensione automatica post-consegna (screen 05)."""
    return (
        f"🎉 <b>ORDINE CONSEGNATO!</b>\n\n"
        f"Il pacco dell'ordine <code>#{order_id}</code> è arrivato a destinazione.\n\n"
        f"Ti andrebbe di valutare il tuo acquisto?\n"
        f"La tua opinione ci aiuta a migliorare 🙏"
    )


def format_admin_dashboard(
    pending_count: int,
    today_revenue: float,
    active_products: int,
    total_customers: int,
    month_revenue: float,
    avg_rating: float,
) -> str:
    """
    Testo dashboard admin (screen 06).
    KPI: ordini da evadere, incasso oggi/mese, prodotti, clienti, rating.
    """
    return (
        f"📊 <b>DASHBOARD — Oro Naturale</b>\n\n"
        f"📦 Ordini da evadere:  <b>{pending_count}</b>\n"
        f"💶 Incasso oggi:       <b>€ {today_revenue:.2f}</b>\n"
        f"👕 Prodotti attivi:    <b>{active_products}</b>\n"
        f"👥 Clienti totali:     <b>{total_customers}</b>\n"
        f"📈 Incasso mese:       <b>€ {month_revenue:.2f}</b>\n"
        f"⭐ Rating medio:       <b>{avg_rating:.1f} / 5</b>"
    )


def format_admin_new_order(
    order_id: str,
    customer_name: str,
    username: str | None,
    address: str,
    items_text: str,
    total: float,
    gateway: str = "Stripe",
) -> str:
    """
    Testo notifica nuovo ordine su canale admin (screen 08).
    Inviato automaticamente al completamento del pagamento.
    """
    user_ref = f"(@{username})" if username else ""
    return (
        f"🔔 <b>NUOVO ORDINE CONFERMATO</b>\n"
        f"<code>#{order_id}</code>\n\n"
        f"👤 <b>CLIENTE:</b>\n"
        f"{customer_name} {user_ref}\n\n"
        f"📍 <b>DESTINAZIONE:</b>\n"
        f"{address}\n\n"
        f"🛍 <b>PRODOTTI:</b>\n"
        f"{items_text}\n\n"
        f"💰 <b>TOTALE PAGATO:</b> € {total:.2f}\n"
        f"💳 <b>GATEWAY:</b> {gateway} ✅"
    )


def format_category_header(category: str, product_count: int, page: int = 0) -> str:
    meta      = CATEGORY_META.get(category, {})
    emoji     = meta.get("emoji", "📦")
    label     = meta.get("label", category.replace("_", " ").title())
    page_info = f" — Pagina {page + 1}" if page > 0 else ""
    return f"{emoji} <b>{label}</b>\n\n<i>{product_count} prodotti disponibili{page_info}</i>"


def format_featured_header(product_count: int) -> str:
    return f"⭐ <b>In evidenza</b>\n\n<i>{product_count} prodotti selezionati per te</i>"


def format_search_header(query: str, result_count: int) -> str:
    return f"🔍 <b>Risultati per \"{query}\":</b>  {result_count} trovati"


def format_search_empty(query: str) -> str:
    return (
        f"😕 Nessun risultato per <b>\"{query}\"</b>.\n\n"
        "Prova con un'altra parola chiave."
    )


def format_profile(user, cart_count: int, fav_count: int) -> str:
    return (
        f"👤 <b>Il tuo profilo</b>\n\n"
        f"📛 Nome: <b>{user.full_name}</b>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🌐 Username: @{user.username or '—'}\n\n"
        f"🛒 Nel carrello: <b>{cart_count}</b>\n"
        f"❤️ Preferiti: <b>{fav_count}</b>"
    )


def format_store_info() -> str:
    return (
        "📍 <b>Oro Naturale</b>\n\n"
        "🏪 Via Roma 1, 06083 Bastia Umbra (PG)\n"
        "📞 +39 075 0000000\n"
        "✉️ info@oronaturale.it\n\n"
        "🕐 <b>Orari:</b>\n"
        "Lun–Ven: 9:00 – 19:00\n"
        "Sab: 9:00 – 13:00\n"
        "Dom: chiuso\n\n"
        "🚗 <i>Uscita Bastia Umbra del SS75</i>"
    )


def format_support_info() -> str:
    return (
        "🎧 <b>Supporto clienti</b>\n\n"
        "Siamo qui per aiutarti!\n"
        "Tempo medio di risposta: <b>< 2 ore</b> 🕐"
    )


def format_favorites_empty() -> str:
    return (
        "❤️ <b>Preferiti</b>\n\n"
        "Non hai ancora salvato nessun prodotto.\n"
        "Sfoglia il catalogo e premi 🤍 su ciò che ti piace!"
    )


def format_favorites_header(count: int) -> str:
    return f"❤️ <b>Preferiti</b>  ({count} prodotti salvati)"
