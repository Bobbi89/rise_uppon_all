from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🛒 Catalogo"),
        KeyboardButton(text="🛍️ Carrello"),
    )
    builder.row(
        KeyboardButton(text="📝 Fai un ordine"),
        KeyboardButton(text="💳 Pagamenti"),
    )
    builder.row(
        KeyboardButton(text="📦 Spedizione"),
        KeyboardButton(text="📞 Contatti"),
    )
    builder.row(
        KeyboardButton(text="🏢 Area B2B"),
        KeyboardButton(text="ℹ️ Info & FAQ"),
    )
    return builder.as_markup(resize_keyboard=True, is_persistent=True)


def categories_menu(categories: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category, label in categories:
        builder.button(text=label, callback_data=f"cat:{category}")
    builder.adjust(2)
    return builder.as_markup()


def quantity_menu(product_name: str, qty: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➖", callback_data=f"qty:{product_name}:{max(1, qty - 1)}")
    builder.button(text=f"Q.tà {qty}", callback_data="noop")
    builder.button(text="➕", callback_data=f"qty:{product_name}:{qty + 1}")
    builder.button(text="Aggiungi al carrello", callback_data=f"add:{product_name}:{qty}")
    builder.adjust(3, 1)
    return builder.as_markup()


def cart_menu(items: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, key in items:
        builder.button(text=f"Rimuovi {label}", callback_data=f"rem:{key}")
    builder.button(text="Inserisci dati spedizione", callback_data="checkout_data")
    builder.button(text="Svuota carrello", callback_data="cart_clear")
    builder.adjust(1)
    return builder.as_markup()


def admin_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="/orders"),
        KeyboardButton(text="/payments"),
    )
    builder.row(
        KeyboardButton(text="/shipping_list"),
        KeyboardButton(text="/pagamenti"),
    )
    return builder.as_markup(resize_keyboard=True)
