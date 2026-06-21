# ═══════════════════════════════════════════════════════════════════
#  Oro Naturale — Keyboards
#  Tutte le tastiere inline e reply del bot
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
        "emoji": "\U0001f33f",
        "label": "Oli Extravergine",
    },
    "flavored_oil": {
        "emoji": "\U0001f9c3",
        "label": "Oli Aromatizzati",
    },
    "wine": {
        "emoji": "\U0001f377",
        "label": "Vini",
    },
    "cosmetics": {
        "emoji": "\U0001f9f4",
        "label": "Cosmetica",
    },
    "gift_box": {
        "emoji": "\U0001f381",
        "label": "Gift Box",
    },
}


# ═══════════════════════════════════════════════════════════════════
#  HELPER
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
#  REPLY KEYBOARD — Menu principale
# ═══════════════════════════════════════════════════════════════════

def main_menu(cart_count: int = 0) -> ReplyKeyboardMarkup:
    """Menu principale fisso — 4 righe x 2 colonne."""
    cart_label = f"\U0001f6d2 Carrello ({cart_count})" if cart_count > 0 else "\U0001f6d2 Carrello"
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="\U0001f6cd\ufe0f Catalogo"),
                KeyboardButton(text="\U0001f50d Cerca"),
            ],
            [
                KeyboardButton(text=cart_label),
                KeyboardButton(text="\U0001f4e6 I miei ordini"),
            ],
            [
                KeyboardButton(text="\u2764\ufe0f Preferiti"),
                KeyboardButton(text="\U0001f464 Profilo"),
            ],
            [
                KeyboardButton(text="\U0001f4cd Negozio"),
                KeyboardButton(text="\U0001f3a7 Supporto"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def back_only() -> ReplyKeyboardMarkup:
    """Mini keyboard con solo torna al menu."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="\U0001f519 Menu principale")]],
        resize_keyboard=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  INLINE KEYBOARD — Categorie
# ═══════════════════════════════════════════════════════════════════

def categories_menu(
    featured_ids: list[str] | None = None,
) -> InlineKeyboardMarkup:
    """
    Griglia categorie: 2 bottoni per riga.
    Se ci sono prodotti in evidenza, aggiunge riga In evidenza.
    """
    rows: list[list[InlineKeyboardButton]] = []
    cats = list(CATEGORY_META.items())

    for i in range(0, len(cats), 2):
        row: list[InlineKeyboardButton] = []
        for key, meta in cats[i : i + 2]:
            row.append(
                _btn(f"{meta['emoji']} {meta['label']}", f"cat:{key}")
            )
        rows.append(row)

    if featured_ids:
        rows.append([_btn("\u2b50 In evidenza", "cat:featured")])

    return _ikb(*rows)


# ═══════════════════════════════════════════════════════════════════
#  INLINE KEYBOARD — Lista prodotti
# ═══════════════════════════════════════════════════════════════════

def product_list_menu(
    products: list[dict],
    category: str,
    page: int = 0,
    per_page: int = 10,
) -> InlineKeyboardMarkup:
    """Lista prodotti con paginazione."""
    rows: list[list[InlineKeyboardButton]] = []

    start = page * per_page
    end = start + per_page
    page_items = products[start:end]

    for p in page_items:
        pid = p.get("id", "")
        name = p.get("name", "Prodotto")
        price = p.get("price", 0.0)
        stock = int(p.get("stock", 0))

        out_of_stock = "\u26d4 " if stock <= 0 else ""
        price_str = f"\u20ac{float(price):.2f}"

        featured_badge = " \u2b50" if p.get("featured") == "true" or p.get("featured") is True else ""

        label = f"{out_of_stock}{name} \u2014 {price_str}{featured_badge}"
        rows.append([_btn(label, f"prod:{pid}")])

    nav_row: list[InlineKeyboardButton] = []
    total_pages = max(1, (len(products) + per_page - 1) // per_page)

    if page > 0:
        nav_row.append(_btn("\u25c0 Pagina precedente", f"cat_page:{category}:{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(_btn("Pagina successiva \u25b6", f"cat_page:{category}:{page + 1}"))

    if nav_row:
        rows.append(nav_row)

    rows.append(
        [
            _btn("\u25c0 Categorie", "show_categories"),
            _btn("\U0001f3e0 Menu", "main_menu"),
        ]
    )

    return _ikb(*rows)


# ═══════════════════════════════════════════════════════════════════
#  INLINE KEYBOARD — Scheda prodotto
# ═══════════════════════════════════════════════════════════════════

def product_card_menu(
    product_id: str,
    category: str,
    stock: int,
    is_fav: bool = False,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if stock > 0:
        rows.append([_btn("\U0001f6d2 Aggiungi al carrello", f"add:{product_id}")])
    else:
        rows.append([_btn("\u26d4 Esaurito", "noop")])

    fav_label = "\u2764\ufe0f Salvato" if is_fav else "\U0001f90d Salva"
    rows.append(
        [
            _btn(fav_label, f"fav:{product_id}"),
            _btn("\u2139\ufe0f Dettagli", f"info:{product_id}"),
        ]
    )

    rows.append(
        [
            _btn("\u25c0 Torna alla categoria", f"back_cat:{category}"),
            _btn("\U0001f3e0 Menu", "main_menu"),
        ]
    )

    return _ikb(*rows)


# ═══════════════════════════════════════════════════════════════════
#  INLINE KEYBOARD — Quantita
# ═══════════════════════════════════════════════════════════════════

def quantity_menu(product_id: str, current_qty: int, max_qty: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    qty_row: list[InlineKeyboardButton] = []
    if current_qty > 1:
        qty_row.append(_btn("\u2796 Meno", f"qty:{product_id}:{current_qty - 1}"))
    else:
        qty_row.append(_btn("\U0001f5d1\ufe0f Rimuovi", f"qty:{product_id}:0"))

    qty_row.append(
        _btn(f"\U0001f4cf {current_qty} pezz{'o' if current_qty == 1 else 'i'}", "noop")
    )

    if current_qty < max_qty:
        qty_row.append(_btn("\u2795 Piu", f"qty:{product_id}:{current_qty + 1}"))
    else:
        qty_row.append(_btn("\U0001f6ab Max", "noop"))

    rows.append(qty_row)
    rows.append([_btn("\u25c0 Torna al carrello", "show_cart")])

    return _ikb(*rows)


# ═══════════════════════════════════════════════════════════════════
#  INLINE KEYBOARD — Carrello
# ═══════════════════════════════════════════════════════════════════

def cart_menu(has_items: bool = True) -> InlineKeyboardMarkup:
    if not has_items:
        return _ikb([_btn("\U0001f6cd\ufe0f Vai al catalogo", "show_categories")])

    return _ikb(
        [_btn("\u2705 Procedi al checkout", "checkout_start")],
        [
            _btn("\u270f\ufe0f Modifica quantita", "cart_edit"),
            _btn("\U0001f3f7\ufe0f Inserisci coupon", "cart_coupon"),
        ],
        [
            _btn("\U0001f5d1\ufe0f Svuota carrello", "cart_clear"),
            _btn("\U0001f6cd\ufe0f Continua acquisti", "show_categories"),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
#  INLINE KEYBOARD — Checkout
# ═══════════════════════════════════════════════════════════════════

def shipping_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("\U0001f4e6 Spedizione a casa  (+\u20ac4,90)", "ship:home")],
        [_btn("\U0001f3ea Ritiro in negozio (gratuito)", "ship:pickup")],
        [_btn("\u25c0 Torna al carrello", "show_cart")],
    )


def payment_menu(total: float) -> InlineKeyboardMarkup:
    return _ikb(
        [_btn(f"\U0001f4b3 Paga ora \u2014 \u20ac{total:.2f}", "pay:card")],
        [
            _btn("\U0001f3e6 Bonifico bancario", "pay:bank"),
            _btn("\U0001f4b8 PayPal", "pay:paypal"),
        ],
        [_btn("\u25c0 Modifica spedizione", "checkout_start")],
    )


def order_confirmed_menu(order_id: str) -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("\U0001f4e6 Traccia spedizione", f"track:{order_id}")],
        [
            _btn("\U0001f6cd\ufe0f Continua a comprare", "show_categories"),
            _btn("\U0001f3e0 Menu", "main_menu"),
        ],
    )


def orders_menu(order_list: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for o in order_list:
        rows.append(
            [
                _btn(
                    f"#{o['id']} \u2014 {o['date']} \u2014 \u20ac{o['total']:.2f} {o['status']}",
                    f"order:{o['id']}",
                )
            ]
        )
    rows.append([_btn("\U0001f3e0 Menu principale", "main_menu")])
    return _ikb(*rows)


def search_results_menu(results: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for p in results:
        pid = p.get("id", "")
        name = p.get("name", "Prodotto")
        price = p.get("price", 0.0)
        rows.append([_btn(f"{name} \u2014 \u20ac{float(price):.2f}", f"prod:{pid}")])
    rows.append(
        [
            _btn("\U0001f50d Nuova ricerca", "search_again"),
            _btn("\U0001f3e0 Menu", "main_menu"),
        ]
    )
    return _ikb(*rows)


def search_no_results_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("\U0001f6cd\ufe0f Vai al catalogo", "show_categories")],
        [_btn("\U0001f3e0 Menu", "main_menu")],
    )


def favorites_menu(products: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for p in products:
        pid = p.get("id", "")
        name = p.get("name", "Prodotto")
        price = p.get("price", 0.0)
        rows.append([_btn(f"{name} \u2014 \u20ac{float(price):.2f}", f"prod:{pid}")])
    rows.append([_btn("\U0001f6cd\ufe0f Vai al catalogo", "show_categories")])
    return _ikb(*rows)


def favorites_empty_menu() -> InlineKeyboardMarkup:
    return _ikb([_btn("\U0001f6cd\ufe0f Vai al catalogo", "show_categories")])


def profile_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("\U0001f4cb I miei ordini", "orders_list")],
        [_btn("\u2764\ufe0f Preferiti", "fav_list")],
        [_btn("\U0001f3e0 Menu", "main_menu")],
    )


def store_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn_url("\U0001f5fa\ufe0f Apri su Google Maps", "https://maps.google.com")],
        [_btn("\U0001f3e0 Menu", "main_menu")],
    )


def support_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("\U0001f4ac Scrivi all'operatore", "support_write")],
        [_btn_url("\U0001f4de Chiama il negozio", "tel:+390000000000")],
        [_btn("\U0001f3e0 Menu", "main_menu")],
    )


def back_to_categories_menu() -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("\u25c0 Categorie", "show_categories")],
        [_btn("\U0001f3e0 Menu", "main_menu")],
    )


def back_to_cart_menu() -> InlineKeyboardMarkup:
    return _ikb([_btn("\u25c0 Torna al carrello", "show_cart")])


def back_to_shipping_menu() -> InlineKeyboardMarkup:
    return _ikb([_btn("\u25c0 Modifica spedizione", "checkout_start")])


def order_detail_menu(order_id: str) -> InlineKeyboardMarkup:
    return _ikb(
        [_btn("\U0001f4e6 Traccia spedizione", f"track:{order_id}")],
        [
            _btn("\u25c0 I miei ordini", "orders_list"),
            _btn("\U0001f3e0 Menu", "main_menu"),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
#  FORMATTERS — Testo schede e riepiloghi
# ═══════════════════════════════════════════════════════════════════

def format_product_card(p: dict) -> str:
    """Genera il testo della scheda prodotto."""
    name = p.get("name", "Prodotto")
    description = p.get("description", "")
    price = p.get("price", 0.0)
    stock = int(p.get("stock", 0))
    category = p.get("category", "")
    details = p.get("details", {})
    featured = p.get("featured")
    is_featured = featured is True or featured == "true"

    badge_line = ""
    if is_featured:
        badge_line = "\n\u2b50 <b>In evidenza</b>"

    if stock <= 0:
        stock_line = "\n\u26d4 <b>Esaurito</b>"
    elif stock <= 5:
        stock_line = f"\n\u26a0\ufe0f Solo {stock} rimast{'o' if stock == 1 else 'i'}!"
    else:
        stock_line = f"\n\u2705 Disponibile ({stock} pezzi)"

    detail_lines: list[str] = []
    if isinstance(details, dict):
        origin = details.get("origin")
        if origin:
            detail_lines.append(f"\U0001f4cd Origine: {origin}")
        volume = details.get("volume")
        if volume:
            detail_lines.append(f"\U0001f4e6 Formato: {volume}")
        harvest = details.get("harvest_year")
        if harvest:
            detail_lines.append(f"\U0001f33e Raccolto: {harvest}")
        characteristics = details.get("characteristics")
        if isinstance(characteristics, list) and characteristics:
            chars_str = " \u00b7 ".join(characteristics)
            detail_lines.append(f"\U0001f3af {chars_str}")

    details_text = "\n".join(detail_lines) if detail_lines else ""

    cat_meta = CATEGORY_META.get(category, {})
    cat_label = cat_meta.get("label", category.replace("_", " ").title())
    cat_emoji = cat_meta.get("emoji", "\U0001f4e6")

    text = (
        f"{cat_emoji} <b>{name}</b>{badge_line}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"{description}\n"
    )
    if details_text:
        text += f"\n{details_text}\n"
    text += (
        f"{stock_line}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4b0 <b>\u20ac {float(price):.2f}</b>\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f447 Cosa vuoi fare?"
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
    """Restituisce (testo riepilogo carrello, totale finale)."""
    if not cart_items:
        return (
            "\U0001f6d2 Il tuo carrello e' <b>vuoto</b>.\n\n"
            "Aggiungi qualcosa dal catalogo!",
            0.0,
        )

    lines: list[str] = ["\U0001f6d2 <b>Il tuo carrello</b>\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"]
    subtotal = 0.0
    total_pieces = 0

    for item in cart_items:
        pid = item.get("product_id", "")
        qty = item.get("qty", 0)
        p = products_map.get(pid)
        if not p:
            continue

        name = p.get("name", "Prodotto")
        price = float(p.get("price", 0.0))
        row_total = price * qty
        subtotal += row_total
        total_pieces += qty

        lines.append(f"\U0001f33f {name}  x{qty}  \u2192  <b>\u20ac {row_total:.2f}</b>")

    if shipping == "home":
        lines.append(f"\n\U0001f4e6 Spedizione a casa:  \u20ac {shipping_cost:.2f}")
    elif shipping == "pickup":
        lines.append("\n\U0001f3ea Ritiro in negozio:  <b>Gratuito</b>")

    if coupon and discount > 0:
        disc_amount = subtotal * discount
        disc_pct = int(discount * 100)
        lines.append(f"\U0001f3f7\ufe0f Sconto coupon ({disc_pct}%):  <b>\u2212\u20ac {disc_amount:.2f}</b>")

    total = max(0.0, (subtotal + shipping_cost) * (1 - discount))
    lines.append("\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501")
    lines.append(f"\U0001f4b4 <b>Totale: \u20ac {total:.2f}</b>  ({total_pieces} articol{'o' if total_pieces == 1 else 'i'})")

    return "\n".join(lines), total


def format_category_header(category: str, product_count: int, page: int = 0) -> str:
    meta = CATEGORY_META.get(category, {})
    emoji = meta.get("emoji", "\U0001f4e6")
    label = meta.get("label", category.replace("_", " ").title())

    page_info = f" \u2014 Pagina {page + 1}" if page > 0 else ""
    return f"{emoji} <b>{label}</b>\n\n<i>{product_count} prodotti disponibili{page_info}</i>"


def format_featured_header(product_count: int) -> str:
    return f"\u2b50 <b>In evidenza</b>\n\n<i>{product_count} prodotti selezionati per te</i>"


def format_search_header(query: str, result_count: int) -> str:
    return f"\U0001f50d <b>Risultati per \"{query}\":</b>  {result_count} trovati"


def format_search_empty(query: str) -> str:
    return (
        f"\U0001f615 Nessun risultato per <b>\"{query}\"</b>.\n\n"
        "Prova con un'altra parola chiave."
    )


def format_order_confirmed(
    order_id: str,
    total: float,
    method_label: str,
    shipping_label: str,
    address: str | None = None,
) -> str:
    text = (
        f"\u2705 <b>Ordine confermato!</b>\n\n"
        f"\U0001f4cb Numero: <code>{order_id}</code>\n"
        f"\U0001f4b4 Totale: <b>\u20ac {total:.2f}</b>\n"
        f"\U0001f4b3 Metodo: {method_label}\n"
        f"\U0001f6e2\ufe0f Spedizione: {shipping_label}\n"
    )
    if address:
        text += f"\U0001f4cd Indirizzo: <b>{address}</b>\n"
    text += (
        f"\nRiceverai una notifica quando il pacco sara' spedito \U0001f4e6\n"
        f"Grazie per aver acquistato da <b>Oro Naturale</b>! \U0001f64f"
    )
    return text


def format_order_detail(order: dict) -> str:
    order_id = order.get("id", "")
    date = order.get("date", "")
    status = order.get("status", "")
    total = float(order.get("total", 0.0))
    items = order.get("items", "")

    text = (
        f"\U0001f4cb <b>Ordine {order_id}</b>\n\n"
        f"\U0001f4c5 Data: {date}\n"
        f"\U0001f4e6 Stato: {status}\n"
    )
    if items:
        text += f"\n{items}\n"
    text += (
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4b4 <b>Totale: \u20ac {total:.2f}</b>\n\n"
        f"<i>Riceverai un SMS con il link di tracciamento.</i>"
    )
    return text


def format_profile(user, cart_count: int, fav_count: int) -> str:
    return (
        f"\U0001f464 <b>Il tuo profilo</b>\n\n"
        f"\U0001f4db Nome: <b>{user.full_name}</b>\n"
        f"\U0001f194 ID: <code>{user.id}</code>\n"
        f"\U0001f310 Username: @{user.username or '\u2014'}\n\n"
        f"\U0001f6d2 Nel carrello: <b>{cart_count}</b>\n"
        f"\u2764\ufe0f Preferiti: <b>{fav_count}</b>"
    )


def format_store_info() -> str:
    return (
        "\U0001f4cd <b>Oro Naturale</b>\n\n"
        "\U0001f3ea Via Roma 1, 06083 Bastia Umbra (PG)\n"
        "\U0001f4de +39 075 0000000\n"
        "\u2709\ufe0f info@oronaturale.it\n\n"
        "\U0001f550 <b>Orari:</b>\n"
        "Lun\u2013Ven: 9:00 \u2013 19:00\n"
        "Sab: 9:00 \u2013 13:00\n"
        "Dom: chiuso\n\n"
        "\U0001f687 <i>Prossimita: uscita Bastia Umbra del SS75</i>"
    )


def format_support_info() -> str:
    return (
        "\U0001f3a7 <b>Supporto clienti</b>\n\n"
        "Siamo qui per aiutarti!\n"
        "Tempo medio di risposta: <b>< 2 ore</b> \U0001f550"
    )


def format_favorites_empty() -> str:
    return (
        "\u2764\ufe0f <b>Preferiti</b>\n\n"
        "Non hai ancora salvato nessun prodotto.\n"
        "Sfoglia il catalogo e premi \U0001f90d su cio' che ti piace!"
    )


def format_favorites_header(count: int) -> str:
    return f"\u2764\ufe0f <b>Preferiti</b>  ({count} prodotti salvati)"