# routers/public.py
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from ..context import BotContext
from ..catalog import product_price_value, product_key
from ..keyboards import (
    main_menu, categories_menu, product_list_menu, product_card_menu,
    cart_menu, store_menu,
    format_category_header, format_product_card, format_store_info
)


def build_public_router(ctx: BotContext) -> Router:
    router = Router()

    @router.message(Command("start"))
    async def cmd_start(message: Message):
        await message.answer(
            "👋 Ciao! Benvenuto su <b>Oro Naturale</b>.\n\n"
            "Sfoglia il nostro catalogo di oli, vini e cosmetici!",
            reply_markup=main_menu()
        )

    @router.message(F.text == "🛍️ Catalogo")
    async def txt_catalog(message: Message):
        featured_ids = [p.id or product_key(p) for p in ctx.products if p.featured.lower() == "true"]
        await message.answer(
            "📂 <b>Scegli una categoria:</b>",
            reply_markup=categories_menu(featured_ids if featured_ids else None)
        )

    @router.message(F.text == "🛒 Carrello")
    async def txt_cart(message: Message):
        # Carrello vuoto per ora
        await message.answer(
            "🛒 Il tuo carrello è <b>vuoto</b>.\n\nAggiungi qualcosa dal catalogo!",
            reply_markup=cart_menu(has_items=False)
        )

    @router.message(F.text == "📍 Negozio")
    async def txt_store(message: Message):
        await message.answer(format_store_info(), reply_markup=store_menu())

    @router.callback_query(F.data == "show_categories")
    async def cb_show_categories(callback: CallbackQuery):
        featured_ids = [p.id or product_key(p) for p in ctx.products if p.featured.lower() == "true"]
        await callback.message.edit_text(
            "📂 <b>Scegli una categoria:</b>",
            reply_markup=categories_menu(featured_ids if featured_ids else None)
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("cat:"))
    @router.callback_query(F.data.startswith("cat_page:"))
    async def cb_show_products(callback: CallbackQuery):
        data = callback.data
        page = 0
        if data.startswith("cat_page:"):
            parts = data.split(":")
            category = parts[1]
            page = int(parts[2])
        else:
            category = data.split(":", 1)[1]
            
        if category == "featured":
            prods = [p for p in ctx.products if p.featured.lower() == "true"]
        else:
            prods = [p for p in ctx.products if p.category == category]
            
        if not prods:
            await callback.answer("Nessun prodotto in questa categoria.", show_alert=True)
            return
            
        prod_dicts = []
        for p in prods:
            price = product_price_value(p) or 0.0
            prod_dicts.append({
                "id": p.id or product_key(p),
                "name": p.name,
                "price": price,
                "stock": int(p.stock) if p.stock.isdigit() else 0,
                "featured": p.featured
            })
            
        header = format_category_header(category, len(prods), page)
        kb = product_list_menu(prod_dicts, category, page)
        
        await callback.message.edit_text(header, reply_markup=kb)
        await callback.answer()

    @router.callback_query(F.data.startswith("back_cat:"))
    async def cb_back_to_cat(callback: CallbackQuery):
        category = callback.data.split(":", 1)[1]
        # Simuliamo il click sulla categoria per riutilizzare la logica
        callback.data = f"cat:{category}"
        await cb_show_products(callback)

    @router.callback_query(F.data.startswith("prod:"))
    async def cb_show_product(callback: CallbackQuery):
        pid = callback.data.split(":", 1)[1]
        product = next((p for p in ctx.products if (p.id or product_key(p)) == pid), None)
        
        if not product:
            await callback.answer("Prodotto non trovato.", show_alert=True)
            return
            
        price = product_price_value(product) or 0.0
        stock = int(product.stock) if product.stock.isdigit() else 0
        
        prod_dict = {
            "id": product.id or product_key(product),
            "name": product.name,
            "description": product.description,
            "price": price,
            "stock": stock,
            "category": product.category,
            "details": product.details,
            "featured": product.featured
        }
        
        text = format_product_card(prod_dict)
        kb = product_card_menu(prod_dict["id"], product.category, stock)
        
        # Se c'è un'immagine, mandiamo una nuova foto, altrimenti editiamo il testo
        if product.image_url:
            await callback.message.answer_photo(
                photo=product.image_url,
                caption=text,
                reply_markup=kb
            )
            try:
                await callback.message.delete()
            except:
                pass
        else:
            await callback.message.edit_text(text, reply_markup=kb)
            
        await callback.answer()

    @router.callback_query(F.data == "main_menu")
    async def cb_main_menu(callback: CallbackQuery):
        await callback.message.edit_text(
            "🏠 Sei al menu principale.\nUsa la tastiera in basso per continuare."
        )
        await callback.answer()

    return router