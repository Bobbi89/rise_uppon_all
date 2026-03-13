import asyncio
import csv
import os
from dataclasses import dataclass
from typing import Dict, List

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv


@dataclass
class Product:
    name: str
    description: str
    price: str
    category: str
    featured: str
    stock: str


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()

if not TOKEN:
    raise SystemExit("Missing TELEGRAM_BOT_TOKEN in .env")

PRODUCTS_CSV = os.getenv("PRODUCTS_CSV", "Product_export.csv")

PROMO_MESSAGE = (
    "Oro Naturale - EVO artigianale dall'Umbria.\n"
    "Catalogo: /catalogo\n"
    "Spedizione gratuita da EUR 100.\n"
    "Dimmi l'occasione e ti consiglio l'olio giusto."
)

ORDER_TEMPLATE = (
    "Per preparare l'ordine, inviami:\n"
    "- Nome e Cognome\n"
    "- Indirizzo completo (via, numero, CAP, citta, paese)\n"
    "- Email (per ricevuta)\n"
    "- Telefono (opzionale)\n"
    "- Prodotti e quantita\n"
    "Ti rispondo con totale e istruzioni di pagamento."
)

CATEGORY_LABELS = {
    "extra_virgin_olive_oil": "Olio Extravergine di Oliva",
    "flavored_oil": "Oli Aromatizzati",
    "wine": "Vini",
    "cosmetics": "Cosmetici all'olio d'oliva",
    "gift_box": "Confezioni Regalo",
    "food": "Gourmet",
}


def load_products(path: str) -> List[Product]:
    items: List[Product] = []
    if not os.path.exists(path):
        return items
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(
                Product(
                    name=row.get("name", "").strip(),
                    description=row.get("description", "").strip(),
                    price=row.get("price", "").strip(),
                    category=row.get("category", "").strip(),
                    featured=row.get("featured", "").strip(),
                    stock=row.get("stock", "").strip(),
                )
            )
    return items


def group_by_category(products: List[Product]) -> Dict[str, List[Product]]:
    grouped: Dict[str, List[Product]] = {}
    for p in products:
        grouped.setdefault(p.category or "other", []).append(p)
    return grouped


def format_products(items: List[Product], limit: int = 12) -> str:
    lines = []
    for p in items[:limit]:
        price = f"EUR {p.price}" if p.price else "Prezzo su richiesta"
        name = p.name or "Prodotto"
        lines.append(f"- {name} - {price}")
    if not lines:
        return "Nessun prodotto disponibile."
    return "\n".join(lines)


def label_for_category(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def build_catalog_message(products: List[Product]) -> str:
    grouped = group_by_category(products)
    parts = []
    for category in sorted(grouped.keys()):
        label = label_for_category(category)
        parts.append(label)
        parts.append(format_products(grouped[category], limit=8))
        parts.append("")
    if not parts:
        return "Catalogo non disponibile."
    return "\n".join(parts).strip()


def extract_keywords(text: str) -> str:
    t = text.lower()
    if "catalogo" in t or "prodotti" in t:
        return "catalogo"
    if "olio" in t:
        return "olio"
    if "aromat" in t:
        return "aromatizzati"
    if "vino" in t or "vini" in t:
        return "vini"
    if "cosmet" in t:
        return "cosmetici"
    if "gift" in t or "regalo" in t:
        return "gift"
    if "prezzo" in t or "costa" in t:
        return "prezzi"
    if "spedizion" in t or "shipping" in t:
        return "spedizione"
    if "ordine" in t or "compr" in t:
        return "ordine"
    return ""


products_cache = load_products(PRODUCTS_CSV)
promo_tasks: Dict[int, asyncio.Task] = {}


dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Benvenuto su Oro Naturale.\n"
        "Comandi:\n"
        "/catalogo - tutti i prodotti\n"
        "/olio - extravergini\n"
        "/aromatizzati - oli aromatizzati\n"
        "/vini - vini e spumanti\n"
        "/cosmetici - cosmetici\n"
        "/gift - confezioni regalo\n"
        "/ordine - invia dati ordine\n"
        "/promo - messaggio promozionale\n"
        "/promo_on <ore> - promo automatiche nel gruppo\n"
        "/promo_off - stop promo automatiche"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await cmd_start(message)


@dp.message(Command("catalogo"))
async def cmd_catalogo(message: Message) -> None:
    text = build_catalog_message(products_cache)
    await message.answer(text)


@dp.message(Command("olio"))
async def cmd_olio(message: Message) -> None:
    oils = [p for p in products_cache if p.category == "extra_virgin_olive_oil"]
    await message.answer(
        "Oli extravergine disponibili:\n" + format_products(oils, limit=12)
    )


@dp.message(Command("aromatizzati"))
async def cmd_aromatizzati(message: Message) -> None:
    oils = [p for p in products_cache if p.category == "flavored_oil"]
    await message.answer(
        "Oli aromatizzati disponibili:\n" + format_products(oils, limit=12)
    )


@dp.message(Command("vini"))
async def cmd_vini(message: Message) -> None:
    wines = [p for p in products_cache if p.category == "wine"]
    await message.answer("Vini disponibili:\n" + format_products(wines, limit=12))


@dp.message(Command("cosmetici"))
async def cmd_cosmetici(message: Message) -> None:
    items = [p for p in products_cache if p.category == "cosmetics"]
    await message.answer(
        "Cosmetici disponibili:\n" + format_products(items, limit=12)
    )


@dp.message(Command("gift"))
async def cmd_gift(message: Message) -> None:
    items = [p for p in products_cache if p.category == "gift_box"]
    await message.answer(
        "Confezioni regalo:\n" + format_products(items, limit=12)
    )


@dp.message(Command("promo"))
async def cmd_promo(message: Message) -> None:
    await message.answer(PROMO_MESSAGE)


async def promo_loop(bot: Bot, chat_id: int, hours: float) -> None:
    while True:
        await bot.send_message(chat_id, PROMO_MESSAGE)
        await asyncio.sleep(max(1.0, hours) * 3600)


@dp.message(Command("promo_on"))
async def cmd_promo_on(message: Message) -> None:
    parts = message.text.split() if message.text else []
    hours = 6.0
    if len(parts) > 1:
        try:
            hours = float(parts[1])
        except ValueError:
            hours = 6.0
    if message.chat.id in promo_tasks:
        await message.answer("Promo automatiche gia attive qui.")
        return
    task = asyncio.create_task(promo_loop(message.bot, message.chat.id, hours))
    promo_tasks[message.chat.id] = task
    await message.answer(f"Promo automatiche attive ogni {hours} ore.")


@dp.message(Command("promo_off"))
async def cmd_promo_off(message: Message) -> None:
    task = promo_tasks.pop(message.chat.id, None)
    if task:
        task.cancel()
        await message.answer("Promo automatiche disattivate.")
    else:
        await message.answer("Nessuna promo automatica attiva qui.")


@dp.message(Command("ordine"))
async def cmd_ordine(message: Message) -> None:
    await message.answer(ORDER_TEMPLATE)


@dp.message(F.text)
async def on_text(message: Message) -> None:
    keyword = extract_keywords(message.text or "")
    if keyword == "catalogo":
        await cmd_catalogo(message)
        return
    if keyword == "olio":
        await cmd_olio(message)
        return
    if keyword == "aromatizzati":
        await cmd_aromatizzati(message)
        return
    if keyword == "vini":
        await cmd_vini(message)
        return
    if keyword == "cosmetici":
        await cmd_cosmetici(message)
        return
    if keyword == "gift":
        await cmd_gift(message)
        return
    if keyword == "spedizione":
        await message.answer(
            "Spedizione gratuita da EUR 100. Dimmi paese e citta per calcolare."
        )
        return
    if keyword == "ordine":
        await message.answer(ORDER_TEMPLATE)
        return
    if keyword == "prezzi":
        await message.answer(
            "Dimmi quali prodotti ti interessano e ti do i prezzi aggiornati."
        )
        return

    await message.answer(
        "Posso aiutarti con catalogo, prezzi e ordine. Scrivi 'catalogo' o usa /catalogo."
    )


async def main() -> None:
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
