import asyncio
import csv
import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

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
DATA_DIR = os.getenv("DATA_DIR", "data")
CUSTOM_PRODUCTS_FILE = os.path.join(DATA_DIR, "custom_products.json")
SKILLS_FILE = os.path.join(DATA_DIR, "skills.json")
SHIPPING_FILE = os.path.join(DATA_DIR, "shipping.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.jsonl")
PAYMENTS_FILE = os.path.join(DATA_DIR, "payments.jsonl")

FREE_SHIPPING_MIN = float(os.getenv("FREE_SHIPPING_MIN", "100"))
DEFAULT_SHIPPING = float(os.getenv("DEFAULT_SHIPPING", "14"))

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

ORDER_SEND_HINT = (
    "Puoi inviare i dettagli con:\n"
    "/ordine_invia <dettagli>\n"
    "oppure scrivendo un messaggio che contiene 'ordine:'"
)

CATEGORY_LABELS = {
    "extra_virgin_olive_oil": "Olio Extravergine di Oliva",
    "flavored_oil": "Oli Aromatizzati",
    "wine": "Vini",
    "cosmetics": "Cosmetici all'olio d'oliva",
    "gift_box": "Confezioni Regalo",
    "food": "Gourmet",
}

ADMIN_IDS = {
    int(x.strip())
    for x in ADMIN_CHAT_ID.split(",")
    if x.strip().isdigit()
}


def is_admin(message: Message) -> bool:
    return bool(ADMIN_IDS) and message.from_user and message.from_user.id in ADMIN_IDS


def ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


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


def load_custom_products() -> List[Product]:
    if not os.path.exists(CUSTOM_PRODUCTS_FILE):
        return []
    with open(CUSTOM_PRODUCTS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    items: List[Product] = []
    for row in raw:
        items.append(
            Product(
                name=str(row.get("name", "")).strip(),
                description=str(row.get("description", "")).strip(),
                price=str(row.get("price", "")).strip(),
                category=str(row.get("category", "")).strip(),
                featured=str(row.get("featured", "false")).strip(),
                stock=str(row.get("stock", "")).strip(),
            )
        )
    return items


def save_custom_products(items: List[Product]) -> None:
    ensure_data_dir()
    raw = []
    for p in items:
        raw.append(
            {
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "category": p.category,
                "featured": p.featured,
                "stock": p.stock,
            }
        )
    with open(CUSTOM_PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)


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

def load_skills() -> Dict[str, str]:
    if not os.path.exists(SKILLS_FILE):
        return {}
    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_skills(skills: Dict[str, str]) -> None:
    ensure_data_dir()
    with open(SKILLS_FILE, "w", encoding="utf-8") as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)


def load_shipping_rules() -> Dict[str, float]:
    if not os.path.exists(SHIPPING_FILE):
        return {}
    with open(SHIPPING_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k.upper(): float(v) for k, v in raw.items()}


def save_shipping_rules(rules: Dict[str, float]) -> None:
    ensure_data_dir()
    with open(SHIPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


def shipping_cost_for(country: str, total: float, rules: Dict[str, float]) -> float:
    if total >= FREE_SHIPPING_MIN:
        return 0.0
    key = country.upper().strip()
    if key in rules:
        return rules[key]
    return DEFAULT_SHIPPING


def append_jsonl(path: str, payload: Dict) -> None:
    ensure_data_dir()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def find_product_by_keyword(products: List[Product], keyword: str) -> List[Product]:
    k = keyword.lower().strip()
    return [p for p in products if k in p.name.lower()]


products_cache = load_products(PRODUCTS_CSV) + load_custom_products()
promo_tasks: Dict[int, asyncio.Task] = {}
skills_cache = load_skills()
shipping_rules = load_shipping_rules()


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
        "/ordine_invia - invia ordine\n"
        "/spedizione <PAESE> <totale> - calcola spedizione\n"
        "/promo - messaggio promozionale\n"
        "/promo_on <ore> - promo automatiche nel gruppo\n"
        "/promo_off - stop promo automatiche\n"
        "/prezzo <nome> - cerca prezzi\n"
        "/pagato <dettagli> - conferma pagamento\n"
        "/admin - pannello admin (solo admin)"
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
    await message.answer(ORDER_TEMPLATE + "\n\n" + ORDER_SEND_HINT)


@dp.message(Command("ordine_invia"))
async def cmd_ordine_invia(message: Message) -> None:
    details = message.text.replace("/ordine_invia", "").strip() if message.text else ""
    if not details:
        await message.answer("Uso: /ordine_invia <dettagli ordine>")
        return
    payload = {
        "ts": int(time.time()),
        "user_id": message.from_user.id if message.from_user else None,
        "username": message.from_user.username if message.from_user else None,
        "chat_id": message.chat.id,
        "details": details,
    }
    append_jsonl(ORDERS_FILE, payload)
    await message.answer(
        "Ordine ricevuto. Ti rispondo a breve con totale e pagamento."
    )
    for admin_id in ADMIN_IDS:
        await message.bot.send_message(
            admin_id,
            "Nuovo ordine:\n"
            f"Utente: @{payload.get('username')}\n"
            f"Dettagli: {details}",
        )


@dp.message(Command("prezzo"))
async def cmd_prezzo(message: Message) -> None:
    parts = message.text.split(maxsplit=1) if message.text else []
    if len(parts) < 2:
        await message.answer("Scrivi: /prezzo <nome prodotto>")
        return
    matches = find_product_by_keyword(products_cache, parts[1])
    await message.answer(format_products(matches, limit=12))


@dp.message(Command("pagato"))
async def cmd_pagato(message: Message) -> None:
    details = message.text.replace("/pagato", "").strip() if message.text else ""
    payload = {
        "ts": int(time.time()),
        "user_id": message.from_user.id if message.from_user else None,
        "username": message.from_user.username if message.from_user else None,
        "chat_id": message.chat.id,
        "details": details,
    }
    append_jsonl(PAYMENTS_FILE, payload)
    await message.answer(
        "Grazie. Ho ricevuto la conferma. Ti aggiorno appena verifichiamo."
    )
    for admin_id in ADMIN_IDS:
        await message.bot.send_message(
            admin_id,
            "Pagamento segnalato:\n"
            f"Utente: @{payload.get('username')}\n"
            f"Dettagli: {details or 'nessun dettaglio'}",
        )


@dp.message(Command("spedizione"))
async def cmd_spedizione(message: Message) -> None:
    parts = message.text.split() if message.text else []
    if len(parts) < 3:
        await message.answer("Uso: /spedizione <PAESE> <totale_carrello>")
        return
    country = parts[1]
    try:
        total = float(parts[2])
    except ValueError:
        await message.answer("Totale non valido.")
        return
    cost = shipping_cost_for(country, total, shipping_rules)
    await message.answer(
        f"Spedizione per {country.upper()}: EUR {cost} (gratis da EUR {FREE_SHIPPING_MIN})."
    )


@dp.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    await message.answer(
        "Admin commands:\n"
        "/orders - ultimi ordini\n"
        "/payments - ultimi pagamenti\n"
        "/shipping_list - regole spedizione\n"
        "/shipping_set <PAESE> <costo>\n"
        "/product_add <nome>|<prezzo>|<categoria>|<descrizione>\n"
        "/product_del <nome>\n"
        "/product_list\n"
        "/skill_add <keyword>|<risposta>\n"
        "/skill_del <keyword>\n"
        "/skill_list\n"
        "/reload - ricarica catalogo"
    )


def tail_jsonl(path: str, limit: int = 5) -> List[Dict]:
    if not os.path.exists(path):
        return []
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    items = [json.loads(l) for l in lines[-limit:]]
    return items


@dp.message(Command("orders"))
async def cmd_orders(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    items = tail_jsonl(ORDERS_FILE, limit=5)
    if not items:
        await message.answer("Nessun ordine registrato.")
        return
    parts = []
    for o in items:
        parts.append(
            f"- {o.get('ts')} | @{o.get('username')} | {o.get('details')}"
        )
    await message.answer("Ultimi ordini:\n" + "\n".join(parts))


@dp.message(Command("payments"))
async def cmd_payments(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    items = tail_jsonl(PAYMENTS_FILE, limit=5)
    if not items:
        await message.answer("Nessun pagamento registrato.")
        return
    parts = []
    for p in items:
        parts.append(
            f"- {p.get('ts')} | @{p.get('username')} | {p.get('details')}"
        )
    await message.answer("Ultimi pagamenti:\n" + "\n".join(parts))


@dp.message(Command("shipping_list"))
async def cmd_shipping_list(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    if not shipping_rules:
        await message.answer("Nessuna regola spedizione. Default attivo.")
        return
    lines = [f"- {k}: EUR {v}" for k, v in shipping_rules.items()]
    await message.answer("Regole spedizione:\n" + "\n".join(lines))


@dp.message(Command("shipping_set"))
async def cmd_shipping_set(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    parts = message.text.split() if message.text else []
    if len(parts) < 3:
        await message.answer("Uso: /shipping_set <PAESE> <costo>")
        return
    country = parts[1].upper()
    try:
        cost = float(parts[2])
    except ValueError:
        await message.answer("Costo non valido.")
        return
    shipping_rules[country] = cost
    save_shipping_rules(shipping_rules)
    await message.answer(f"Regola salvata: {country} = EUR {cost}")


@dp.message(Command("product_add"))
async def cmd_product_add(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    text = message.text.replace("/product_add", "").strip()
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 4:
        await message.answer(
            "Uso: /product_add <nome>|<prezzo>|<categoria>|<descrizione>"
        )
        return
    name, price, category, description = parts[:4]
    custom = load_custom_products()
    custom.append(
        Product(
            name=name,
            description=description,
            price=price,
            category=category,
            featured="false",
            stock="",
        )
    )
    save_custom_products(custom)
    global products_cache
    products_cache = load_products(PRODUCTS_CSV) + load_custom_products()
    await message.answer("Prodotto aggiunto.")


@dp.message(Command("product_del"))
async def cmd_product_del(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    name = message.text.replace("/product_del", "").strip()
    if not name:
        await message.answer("Uso: /product_del <nome>")
        return
    custom = load_custom_products()
    custom = [p for p in custom if p.name.lower() != name.lower()]
    save_custom_products(custom)
    global products_cache
    products_cache = load_products(PRODUCTS_CSV) + load_custom_products()
    await message.answer("Prodotto rimosso (se presente).")


@dp.message(Command("product_list"))
async def cmd_product_list(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    custom = load_custom_products()
    await message.answer("Prodotti custom:\n" + format_products(custom, limit=50))


@dp.message(Command("skill_add"))
async def cmd_skill_add(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    text = message.text.replace("/skill_add", "").strip()
    parts = [p.strip() for p in text.split("|", 1)]
    if len(parts) < 2:
        await message.answer("Uso: /skill_add <keyword>|<risposta>")
        return
    keyword, answer = parts
    skills_cache[keyword.lower()] = answer
    save_skills(skills_cache)
    await message.answer("Skill aggiunta.")


@dp.message(Command("skill_del"))
async def cmd_skill_del(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    key = message.text.replace("/skill_del", "").strip().lower()
    if not key:
        await message.answer("Uso: /skill_del <keyword>")
        return
    skills_cache.pop(key, None)
    save_skills(skills_cache)
    await message.answer("Skill rimossa (se presente).")


@dp.message(Command("skill_list"))
async def cmd_skill_list(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    if not skills_cache:
        await message.answer("Nessuna skill salvata.")
        return
    lines = [f"- {k}" for k in sorted(skills_cache.keys())]
    await message.answer("Skills:\n" + "\n".join(lines))


@dp.message(Command("reload"))
async def cmd_reload(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    global products_cache
    products_cache = load_products(PRODUCTS_CSV) + load_custom_products()
    await message.answer("Catalogo ricaricato.")


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
        details = message.text
        if details and ":" in details:
            payload = {
                "ts": int(time.time()),
                "user_id": message.from_user.id if message.from_user else None,
                "username": message.from_user.username if message.from_user else None,
                "chat_id": message.chat.id,
                "details": details,
            }
            append_jsonl(ORDERS_FILE, payload)
            await message.answer(
                "Ordine ricevuto. Ti rispondo a breve con totale e pagamento."
            )
            for admin_id in ADMIN_IDS:
                await message.bot.send_message(
                    admin_id,
                    "Nuovo ordine:\n"
                    f"Utente: @{payload.get('username')}\n"
                    f"Dettagli: {details}",
                )
        else:
            await message.answer(ORDER_TEMPLATE)
        return
    if keyword == "prezzi":
        await message.answer(
            "Dimmi quali prodotti ti interessano e ti do i prezzi aggiornati."
        )
        return
    if skills_cache:
        text = (message.text or "").lower()
        for key, answer in skills_cache.items():
            if key in text:
                await message.answer(answer)
                return

    await message.answer(
        "Posso aiutarti con catalogo, prezzi e ordine. Scrivi 'catalogo' o usa /catalogo."
    )


async def main() -> None:
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
