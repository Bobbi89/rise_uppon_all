import asyncio
import csv
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

try:
    import stripe  # type: ignore
except Exception:
    stripe = None


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
COMPANY_FILE = os.path.join(DATA_DIR, "company.json")
PAYMENTS_FILE = os.path.join(DATA_DIR, "payments_methods.json")
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
FAQ_FILE = os.path.join(DATA_DIR, "faq.json")
CRYPTO_FILE = os.path.join(DATA_DIR, "crypto_addresses.json")
SEASONAL_FILE = os.path.join(DATA_DIR, "seasonal_promos.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.jsonl")
PAYMENTS_LOG_FILE = os.path.join(DATA_DIR, "payments.jsonl")
SHIPMENTS_FILE = os.path.join(DATA_DIR, "shipments.json")

FREE_SHIPPING_MIN = float(os.getenv("FREE_SHIPPING_MIN", "100"))
DEFAULT_SHIPPING = float(os.getenv("DEFAULT_SHIPPING", "14"))
B2B_DISCOUNT = float(os.getenv("B2B_DISCOUNT", "15"))
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_CURRENCY = os.getenv("STRIPE_CURRENCY", "eur").strip().lower()

PROMO_MESSAGE = (
    "Oro Naturale - EVO artigianale dall'Umbria.\n"
    "Catalogo: /catalogo\n"
    "Spedizione gratuita da EUR 100.\n"
    "Dimmi l'occasione e ti consiglio l'olio giusto."
)

WELCOME_MESSAGE = (
    "Ciao, sono il consulente virtuale Oro Naturale.\n"
    "Ti aiuto a scegliere oli EVO artigianali dall'Umbria per cucina e tavola.\n"
    "Dimmi se cerchi un profilo intenso (Moraiolo) o delicato (Frantoio).\n"
    "Se sei ristoratore o hai Partita IVA applico uno sconto del 15%."
)

ORDER_TEMPLATE = (
    "Per preparare l'ordine, inviami:\n"
    "- Nome e Cognome\n"
    "- Indirizzo completo (via, numero, CAP, citta, paese)\n"
    "- Email (per ricevuta)\n"
    "- Telefono (opzionale)\n"
    "- Prodotti e quantita\n"
    "Ti rispondo con totale, spedizione e istruzioni di pagamento."
)

ORDER_SEND_HINT = (
    "Puoi inviare i dettagli con:\n"
    "/ordine_invia <dettagli>\n"
    "oppure scrivendo un messaggio che contiene 'ordine:'"
)

ORDER_QUICK_REPLY = (
    "Perfetto, ti aiuto subito con l'ordine.\n"
    "Dimmi:\n"
    "- Prodotti e quantita\n"
    "- Paese/citta di consegna\n"
    "Se vuoi, puoi usare /ordine_invia <dettagli>."
)

PAYMENT_FLOW = (
    "Per il pagamento ti invio un link sicuro o le istruzioni in base al metodo scelto.\n"
    "Vedi i metodi con /pagamenti."
)

SHIPPING_FLOW = (
    "Spedizione gratuita da EUR "
    f"{FREE_SHIPPING_MIN}. "
    "Calcola con /spedizione <PAESE> <totale>."
)

LANGS = ["it", "en", "de"]

TEXTS = {
    "it": {
        "welcome": WELCOME_MESSAGE,
        "order_quick": ORDER_QUICK_REPLY,
        "order_template": ORDER_TEMPLATE,
        "order_received": "Ordine ricevuto. Ti rispondo a breve con totale e pagamento.",
        "shipping_flow": SHIPPING_FLOW,
        "payment_flow": PAYMENT_FLOW,
        "ask_lang": "Lingua impostata.",
        "b2b_ack": f"Grazie. Per professionisti applico uno sconto del {B2B_DISCOUNT}%.",
        "faq_title": "Domande frequenti:",
    },
    "en": {
        "welcome": (
            "Hi, I am Oro Naturale virtual consultant.\n"
            "I help you choose artisan EVO oils from Umbria for kitchen and table.\n"
            "Tell me if you prefer intense (Moraiolo) or delicate (Frantoio).\n"
            "If you are a business with VAT, I apply a 15% discount."
        ),
        "order_quick": (
            "Great, I can help with your order.\n"
            "Please share:\n"
            "- Products and quantities\n"
            "- Delivery country/city\n"
            "You can use /ordine_invia <details>."
        ),
        "order_template": (
            "To place the order, please send:\n"
            "- Full name\n"
            "- Full address (street, number, ZIP, city, country)\n"
            "- Email (receipt)\n"
            "- Phone (optional)\n"
            "- Products and quantities\n"
            "I will reply with total, shipping and payment instructions."
        ),
        "order_received": "Order received. I will reply shortly with total and payment.",
        "shipping_flow": (
            f"Free shipping from EUR {FREE_SHIPPING_MIN}. "
            "Use /spedizione <COUNTRY> <total>."
        ),
        "payment_flow": "I will send a secure link or instructions. See /pagamenti.",
        "ask_lang": "Language set.",
        "b2b_ack": f"Thanks. For businesses I apply a {B2B_DISCOUNT}% discount.",
        "faq_title": "FAQ:",
    },
    "de": {
        "welcome": (
            "Hallo, ich bin der virtuelle Berater von Oro Naturale.\n"
            "Ich helfe dir, handwerkliche EVO-Öle aus Umbrien auszuwählen.\n"
            "Magst du intensiv (Moraiolo) oder mild (Frantoio)?\n"
            "Für Geschäftskunden mit USt-IdNr. gibt es 15% Rabatt."
        ),
        "order_quick": (
            "Gerne helfe ich mit der Bestellung.\n"
            "Bitte sende:\n"
            "- Produkte und Mengen\n"
            "- Lieferland/Stadt\n"
            "Du kannst /ordine_invia <details> nutzen."
        ),
        "order_template": (
            "Für die Bestellung brauche ich:\n"
            "- Vor- und Nachname\n"
            "- Vollständige Adresse\n"
            "- E-Mail (Beleg)\n"
            "- Telefon (optional)\n"
            "- Produkte und Mengen\n"
            "Ich antworte mit Gesamtbetrag, Versand und Zahlung."
        ),
        "order_received": "Bestellung erhalten. Ich melde mich mit Gesamtbetrag und Zahlung.",
        "shipping_flow": (
            f"Versand kostenlos ab EUR {FREE_SHIPPING_MIN}. "
            "Nutze /spedizione <LAND> <gesamt>."
        ),
        "payment_flow": "Ich sende einen sicheren Link oder Anweisungen. Siehe /pagamenti.",
        "ask_lang": "Sprache gesetzt.",
        "b2b_ack": f"Danke. Fuer Geschaeftskunden gibt es {B2B_DISCOUNT}% Rabatt.",
        "faq_title": "FAQ:",
    },
}

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
    if "voglio fare un ordine" in t or "fare un ordine" in t:
        return "order_quick"
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


def load_company_info() -> Dict[str, str]:
    if not os.path.exists(COMPANY_FILE):
        return {}
    with open(COMPANY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_company_info(info: Dict[str, str]) -> None:
    ensure_data_dir()
    with open(COMPANY_FILE, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def format_company_info(info: Dict[str, str]) -> str:
    if not info:
        return "Contatti non disponibili. Scrivi all'admin."
    parts = []
    if info.get("name"):
        parts.append(info["name"])
    if info.get("website"):
        parts.append(f"Sito: {info['website']}")
    if info.get("email"):
        parts.append(f"Email: {info['email']}")
    if info.get("phone"):
        parts.append(f"Telefono: {info['phone']}")
    if info.get("whatsapp"):
        parts.append(f"WhatsApp: {info['whatsapp']}")
    if info.get("address"):
        parts.append(f"Indirizzo: {info['address']}")
    if info.get("hours"):
        parts.append(f"Orari: {info['hours']}")
    if info.get("vat"):
        parts.append(f"P.IVA: {info['vat']}")
    return "\n".join(parts)


def load_payment_methods() -> List[str]:
    if not os.path.exists(PAYMENTS_FILE):
        return []
    with open(PAYMENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [str(x) for x in data]


def save_payment_methods(methods: List[str]) -> None:
    ensure_data_dir()
    with open(PAYMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(methods, f, ensure_ascii=False, indent=2)


def format_payment_methods(methods: List[str]) -> str:
    if not methods:
        return "Metodi di pagamento non disponibili. Scrivi all'admin."
    lines = ["Metodi di pagamento:"]
    for m in methods:
        lines.append(f"- {m}")
    return "\n".join(lines)


def load_faq() -> Dict[str, str]:
    if not os.path.exists(FAQ_FILE):
        return {
            "conservazione": "Conserva l'olio in luogo fresco e buio, lontano da fonti di calore.",
            "abbinamenti": "Moraiolo per piatti robusti, Frantoio per piatti delicati.",
            "biologico": "I nostri oli bio sono certificati e tracciati.",
            "certificazioni": "Disponiamo di certificazioni di filiera e bio dove indicato.",
        }
    with open(FAQ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_faq(faq: Dict[str, str]) -> None:
    ensure_data_dir()
    with open(FAQ_FILE, "w", encoding="utf-8") as f:
        json.dump(faq, f, ensure_ascii=False, indent=2)


def load_crypto_addresses() -> Dict[str, str]:
    if not os.path.exists(CRYPTO_FILE):
        return {}
    with open(CRYPTO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_crypto_addresses(data: Dict[str, str]) -> None:
    ensure_data_dir()
    with open(CRYPTO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_seasonal_promos() -> Dict[str, str]:
    if not os.path.exists(SEASONAL_FILE):
        return {
            "christmas": "Promo Natale: gift box e oli speciali. Chiedimi il catalogo.",
            "easter": "Promo Pasqua: selezione oli e vini per la tavola.",
            "summer": "Promo Estate: oli leggeri e aromatizzati.",
        }
    with open(SEASONAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seasonal_promos(data: Dict[str, str]) -> None:
    ensure_data_dir()
    with open(SEASONAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_lang(user_id: Optional[int]) -> str:
    if user_id is None:
        return "it"
    record = customers_cache.get(str(user_id), {})
    return record.get("lang", "it")


def set_lang(user_id: int, lang: str) -> None:
    record = customers_cache.get(str(user_id), {})
    record["lang"] = lang
    customers_cache[str(user_id)] = record
    save_customers(customers_cache)


def get_customer(user_id: Optional[int]) -> Dict[str, str]:
    if user_id is None:
        return {}
    return customers_cache.get(str(user_id), {})


def update_customer(user_id: int, updates: Dict[str, str]) -> None:
    record = customers_cache.get(str(user_id), {})
    record.update(updates)
    customers_cache[str(user_id)] = record
    save_customers(customers_cache)


def t(user_id: Optional[int], key: str) -> str:
    lang = get_lang(user_id)
    return TEXTS.get(lang, TEXTS["it"]).get(key, TEXTS["it"].get(key, ""))


def detect_language(text: str) -> Optional[str]:
    t_ = text.lower()
    if any(k in t_ for k in ["hallo", "bestellung", "versand", "zahlung"]):
        return "de"
    if any(k in t_ for k in ["hello", "order", "shipping", "payment"]):
        return "en"
    if any(k in t_ for k in ["ciao", "ordine", "spedizione", "pagamento"]):
        return "it"
    return None


def parse_total(text: str) -> Optional[float]:
    m = re.search(r"(totale|total|gesamt)[^0-9]*([0-9]+([.,][0-9]+)?)", text, re.I)
    if not m:
        m = re.search(r"([0-9]+([.,][0-9]+)?)\s*(eur|€)", text, re.I)
    if not m:
        return None
    value = m.group(2).replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def parse_country(text: str) -> Optional[str]:
    m = re.search(r"(paese|country|land)[^A-Za-z]*([A-Za-z]{2,})", text, re.I)
    if m:
        return m.group(2).upper()
    for code in shipping_rules.keys():
        if code.lower() in text.lower():
            return code
    return None


def compute_upsell_suggestions(total: float) -> List[Product]:
    gap = FREE_SHIPPING_MIN - total
    if gap <= 0:
        return []
    items: List[Tuple[Product, float]] = []
    for p in products_cache:
        if not p.price:
            continue
        try:
            price = float(p.price.replace(",", "."))
        except ValueError:
            continue
        items.append((p, price))
    items.sort(key=lambda x: x[1])
    suggestions = []
    for p, price in items:
        if price <= gap + 5:
            suggestions.append(p)
        if len(suggestions) >= 3:
            break
    return suggestions


def current_seasonal_promo(promos: Dict[str, str]) -> str:
    tm = time.localtime()
    month = tm.tm_mon
    if month in [12, 1]:
        return promos.get("christmas", PROMO_MESSAGE)
    if month in [3, 4]:
        return promos.get("easter", PROMO_MESSAGE)
    if month in [6, 7, 8]:
        return promos.get("summer", PROMO_MESSAGE)
    return PROMO_MESSAGE


def load_customers() -> Dict[str, Dict[str, str]]:
    if not os.path.exists(CUSTOMERS_FILE):
        return {}
    with open(CUSTOMERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_customers(customers: Dict[str, Dict[str, str]]) -> None:
    ensure_data_dir()
    with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(customers, f, ensure_ascii=False, indent=2)


def detect_b2b(text: str) -> bool:
    t = text.lower()
    return any(
        k in t
        for k in [
            "ristoratore",
            "ristorante",
            "partita iva",
            "p.iva",
            "p iva",
            "azienda",
            "fornitura",
        ]
    )


def detect_preference(text: str) -> Optional[str]:
    t = text.lower()
    if "moraiolo" in t:
        return "moraiolo"
    if "frantoio" in t:
        return "frantoio"
    return None


def parse_payment_method(text: str) -> Optional[str]:
    t = text.lower()
    if "carta" in t or "card" in t or "stripe" in t:
        return "card"
    if "bonifico" in t or "bank" in t:
        return "bank"
    if "crypto" in t or "usdc" in t or "eth" in t or "dai" in t or "sol" in t:
        return "crypto"
    return None


def create_stripe_payment_link(amount: float, currency: str, description: str) -> Optional[str]:
    if not STRIPE_SECRET_KEY or stripe is None:
        return None
    stripe.api_key = STRIPE_SECRET_KEY
    cents = int(round(amount * 100))
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": description or "Oro Naturale order"},
                    "unit_amount": cents,
                },
                "quantity": 1,
            }
        ],
        success_url="https://biomarketshop.com",
        cancel_url="https://biomarketshop.com",
    )
    return session.url


def process_order(details: str, message: Message) -> None:
    total = parse_total(details or "")
    country = parse_country(details or "")
    order_id = f"ON{int(time.time())}"
    payload = {
        "order_id": order_id,
        "ts": int(time.time()),
        "user_id": message.from_user.id if message.from_user else None,
        "username": message.from_user.username if message.from_user else None,
        "chat_id": message.chat.id,
        "details": details,
        "total": total,
        "country": country,
    }
    append_jsonl(ORDERS_FILE, payload)

    reply = t(message.from_user.id if message.from_user else None, "order_received")
    if message.from_user:
        record = get_customer(message.from_user.id)
        if record.get("type") == "b2b" and total:
            discounted = total * (1 - B2B_DISCOUNT / 100.0)
            reply += f"\nTotale B2B: EUR {discounted:.2f}"
        history = record.get("orders", [])
        history.append({"order_id": order_id, "total": total})
        record["orders"] = history[-10:]
        record["stage"] = "payment_pending"
        update_customer(message.from_user.id, record)

    async def _send() -> None:
        await message.answer(reply)
        if total:
            suggestions = compute_upsell_suggestions(total)
            if suggestions:
                await message.answer(
                    "Se aggiungi un prodotto arrivi alla spedizione gratuita:\n"
                    + format_products(suggestions, limit=3)
                )
            method = parse_payment_method(details or "")
            if method == "card" and STRIPE_SECRET_KEY:
                link = create_stripe_payment_link(
                    total, STRIPE_CURRENCY, f"Oro Naturale order {order_id}"
                )
                if link:
                    await message.answer(
                        "Ecco il link di pagamento con carta:\n" + link
                    )
            if method == "crypto" and crypto_cache:
                lines = ["Pagamento crypto disponibile:"]
                for net, addr in crypto_cache.items():
                    lines.append(f"- {net}: {addr}")
                await message.answer("\n".join(lines))
        for admin_id in ADMIN_IDS:
            await message.bot.send_message(
                admin_id,
                "Nuovo ordine:\n"
                f"ID: {order_id}\n"
                f"Utente: @{payload.get('username')}\n"
                f"Totale: {total}\n"
                f"Paese: {country}\n"
                f"Dettagli: {details}",
            )

    asyncio.create_task(_send())


products_cache = load_products(PRODUCTS_CSV) + load_custom_products()
promo_tasks: Dict[int, asyncio.Task] = {}
skills_cache = load_skills()
shipping_rules = load_shipping_rules()
company_info = load_company_info()
payment_methods = load_payment_methods()
customers_cache = load_customers()
faq_cache = load_faq()
crypto_cache = load_crypto_addresses()
seasonal_promos = load_seasonal_promos()


dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        t(message.from_user.id if message.from_user else None, "welcome")
        + "\n\nPer contatti aziendali usa /contatti.\n\nComandi:\n"
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
        "/contatti - info azienda\n"
        "/pagamenti - metodi di pagamento\n"
        "/b2b - attiva sconto professionale\n"
        "/listino_b2b - listino professionale\n"
        "/tracking <order_id>\n"
        "/lingua <it|en|de>\n"
        "/faq\n"
        "/reset\n"
        "/admin - pannello admin (solo admin)"
    )
    if message.from_user:
        update_customer(message.from_user.id, {"stage": "qualify"})


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
    if message.from_user:
        record = customers_cache.get(str(message.from_user.id), {})
        if record.get("type") == "b2b":
            lines = []
            for p in oils:
                try:
                    price = float(p.price.replace(",", "."))
                    disc = price * (1 - B2B_DISCOUNT / 100.0)
                    lines.append(f"- {p.name} - EUR {disc:.2f} (B2B)")
                except Exception:
                    lines.append(f"- {p.name} - EUR {p.price}")
            await message.answer("Listino B2B oli:\n" + "\n".join(lines))
            return
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
    await message.answer(current_seasonal_promo(seasonal_promos))


async def promo_loop(bot: Bot, chat_id: int, hours: float) -> None:
    while True:
        await bot.send_message(chat_id, current_seasonal_promo(seasonal_promos))
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
    await message.answer(
        t(message.from_user.id if message.from_user else None, "order_template")
        + "\n\n"
        + ORDER_SEND_HINT
        + "\n\n"
        + t(message.from_user.id if message.from_user else None, "shipping_flow")
    )


@dp.message(Command("ordine_invia"))
async def cmd_ordine_invia(message: Message) -> None:
    details = message.text.replace("/ordine_invia", "").strip() if message.text else ""
    if not details:
        await message.answer("Uso: /ordine_invia <dettagli ordine>")
        return
    process_order(details, message)


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
    append_jsonl(PAYMENTS_LOG_FILE, payload)
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


@dp.message(Command("b2b"))
async def cmd_b2b(message: Message) -> None:
    if not message.from_user:
        return
    customers_cache[str(message.from_user.id)] = {"type": "b2b"}
    save_customers(customers_cache)
    await message.answer(
        f"Perfetto. Attivo sconto professionale {B2B_DISCOUNT}%.\n"
        "Per applicarlo inviami la Partita IVA e il nome azienda."
    )


@dp.message(Command("listino_b2b"))
async def cmd_listino_b2b(message: Message) -> None:
    if not message.from_user:
        return
    record = customers_cache.get(str(message.from_user.id), {})
    if record.get("type") != "b2b":
        await message.answer("Listino disponibile solo per ristoratori/Partita IVA.")
        return
    oils = [p for p in products_cache if p.category == "extra_virgin_olive_oil"]
    lines = []
    for p in oils:
        try:
            price = float(p.price.replace(",", "."))
            disc = price * (1 - B2B_DISCOUNT / 100.0)
            lines.append(f"- {p.name} - EUR {disc:.2f} (B2B)")
        except Exception:
            lines.append(f"- {p.name} - EUR {p.price}")
    lines.append("Formati 5L/10L disponibili su richiesta.")
    await message.answer("Listino B2B:\n" + "\n".join(lines))


@dp.message(Command("lingua"))
async def cmd_lingua(message: Message) -> None:
    parts = message.text.split() if message.text else []
    if len(parts) < 2 or parts[1] not in LANGS:
        await message.answer("Uso: /lingua it|en|de")
        return
    if message.from_user:
        set_lang(message.from_user.id, parts[1])
    await message.answer(t(message.from_user.id if message.from_user else None, "ask_lang"))


@dp.message(Command("faq"))
async def cmd_faq(message: Message) -> None:
    lines = [t(message.from_user.id if message.from_user else None, "faq_title")]
    for k in sorted(faq_cache.keys()):
        lines.append(f"- {k}")
    await message.answer("\n".join(lines))


@dp.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    if message.from_user:
        update_customer(message.from_user.id, {"stage": "idle"})
    await message.answer("Ok, ripartiamo da zero. Dimmi cosa ti serve.")


@dp.message(Command("tracking"))
async def cmd_tracking(message: Message) -> None:
    parts = message.text.split(maxsplit=1) if message.text else []
    if len(parts) < 2:
        await message.answer("Uso: /tracking <order_id>")
        return
    order_id = parts[1].strip()
    if not os.path.exists(SHIPMENTS_FILE):
        await message.answer("Tracking non disponibile.")
        return
    with open(SHIPMENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    entry = data.get(order_id)
    if not entry:
        await message.answer("Nessuna spedizione trovata per questo ordine.")
        return
    await message.answer(
        f"Tracking {order_id}:\n"
        f"Corriere: {entry.get('carrier')}\n"
        f"Codice: {entry.get('code')}\n"
        f"Stato: {entry.get('status')}\n"
        f"Link: {entry.get('url')}"
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
        "/azienda_set <campo>|<valore>\n"
        "/azienda_view\n"
        "/pagamento_add <metodo>\n"
        "/pagamento_del <metodo>\n"
        "/pagamento_list\n"
        "/tracking_add <order_id>|<carrier>|<code>|<status>|<url>\n"
        "/tracking_del <order_id>\n"
        "/faq_add <keyword>|<risposta>\n"
        "/faq_del <keyword>\n"
        "/faq_list\n"
        "/promo_set <stagione>|<testo>\n"
        "/crypto_set <network>|<address>\n"
        "/crypto_list\n"
        "/checkout <importo> [valuta] [descrizione]\n"
        "/listino_b2b\n"
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
    items = tail_jsonl(PAYMENTS_LOG_FILE, limit=5)
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


@dp.message(Command("contatti"))
async def cmd_contatti(message: Message) -> None:
    await message.answer(format_company_info(company_info))


@dp.message(Command("pagamenti"))
async def cmd_pagamenti(message: Message) -> None:
    text = format_payment_methods(payment_methods)
    if STRIPE_SECRET_KEY:
        text += "\n- Carta (Stripe)"
    if crypto_cache:
        text += "\n- Crypto (USDC/ETH/DAI)"
    await message.answer(text)


@dp.message(Command("azienda_set"))
async def cmd_azienda_set(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    text = message.text.replace("/azienda_set", "").strip()
    parts = [p.strip() for p in text.split("|", 1)]
    if len(parts) < 2:
        await message.answer("Uso: /azienda_set <campo>|<valore>")
        return
    field, value = parts
    company_info[field] = value
    save_company_info(company_info)
    await message.answer("Info azienda aggiornata.")


@dp.message(Command("azienda_view"))
async def cmd_azienda_view(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    await message.answer(format_company_info(company_info))


@dp.message(Command("pagamento_add"))
async def cmd_pagamento_add(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    method = message.text.replace("/pagamento_add", "").strip()
    if not method:
        await message.answer("Uso: /pagamento_add <metodo>")
        return
    if method not in payment_methods:
        payment_methods.append(method)
        save_payment_methods(payment_methods)
    await message.answer("Metodo di pagamento aggiunto.")


@dp.message(Command("pagamento_del"))
async def cmd_pagamento_del(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    method = message.text.replace("/pagamento_del", "").strip()
    if not method:
        await message.answer("Uso: /pagamento_del <metodo>")
        return
    payment_methods[:] = [m for m in payment_methods if m != method]
    save_payment_methods(payment_methods)
    await message.answer("Metodo di pagamento rimosso (se presente).")


@dp.message(Command("pagamento_list"))
async def cmd_pagamento_list(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    await message.answer(format_payment_methods(payment_methods))


@dp.message(Command("crypto_set"))
async def cmd_crypto_set(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    text = message.text.replace("/crypto_set", "").strip()
    parts = [p.strip() for p in text.split("|", 1)]
    if len(parts) < 2:
        await message.answer("Uso: /crypto_set <network>|<address>")
        return
    network, address = parts
    crypto_cache[network.lower()] = address
    save_crypto_addresses(crypto_cache)
    await message.answer("Indirizzo crypto salvato.")


@dp.message(Command("crypto_list"))
async def cmd_crypto_list(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    if not crypto_cache:
        await message.answer("Nessun indirizzo crypto salvato.")
        return
    lines = [f"- {k}: {v}" for k, v in crypto_cache.items()]
    await message.answer("Indirizzi crypto:\n" + "\n".join(lines))


@dp.message(Command("checkout"))
async def cmd_checkout(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    parts = message.text.split(maxsplit=2) if message.text else []
    if len(parts) < 2:
        await message.answer("Uso: /checkout <importo> [valuta] [descrizione]")
        return
    try:
        amount = float(parts[1])
    except ValueError:
        await message.answer("Importo non valido.")
        return
    currency = STRIPE_CURRENCY
    description = "Oro Naturale order"
    if len(parts) >= 3:
        description = parts[2]
    link = create_stripe_payment_link(amount, currency, description)
    if not link:
        await message.answer("Stripe non configurato. Imposta STRIPE_SECRET_KEY.")
        return
    await message.answer(f"Link pagamento: {link}")


@dp.message(Command("tracking_add"))
async def cmd_tracking_add(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    text = message.text.replace("/tracking_add", "").strip()
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 5:
        await message.answer(
            "Uso: /tracking_add <order_id>|<carrier>|<code>|<status>|<url>"
        )
        return
    order_id, carrier, code, status, url = parts[:5]
    data = {}
    if os.path.exists(SHIPMENTS_FILE):
        with open(SHIPMENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    data[order_id] = {
        "carrier": carrier,
        "code": code,
        "status": status,
        "url": url,
    }
    ensure_data_dir()
    with open(SHIPMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    await message.answer("Tracking salvato.")


@dp.message(Command("tracking_del"))
async def cmd_tracking_del(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    order_id = message.text.replace("/tracking_del", "").strip()
    if not order_id:
        await message.answer("Uso: /tracking_del <order_id>")
        return
    if not os.path.exists(SHIPMENTS_FILE):
        await message.answer("Nessun tracking presente.")
        return
    with open(SHIPMENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.pop(order_id, None)
    with open(SHIPMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    await message.answer("Tracking rimosso (se presente).")


@dp.message(Command("faq_add"))
async def cmd_faq_add(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    text = message.text.replace("/faq_add", "").strip()
    parts = [p.strip() for p in text.split("|", 1)]
    if len(parts) < 2:
        await message.answer("Uso: /faq_add <keyword>|<risposta>")
        return
    key, answer = parts
    faq_cache[key.lower()] = answer
    save_faq(faq_cache)
    await message.answer("FAQ aggiunta.")


@dp.message(Command("faq_del"))
async def cmd_faq_del(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    key = message.text.replace("/faq_del", "").strip().lower()
    if not key:
        await message.answer("Uso: /faq_del <keyword>")
        return
    faq_cache.pop(key, None)
    save_faq(faq_cache)
    await message.answer("FAQ rimossa (se presente).")


@dp.message(Command("faq_list"))
async def cmd_faq_list(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    if not faq_cache:
        await message.answer("Nessuna FAQ salvata.")
        return
    lines = [f"- {k}" for k in sorted(faq_cache.keys())]
    await message.answer("FAQ:\n" + "\n".join(lines))


@dp.message(Command("promo_set"))
async def cmd_promo_set(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Comando riservato agli admin.")
        return
    text = message.text.replace("/promo_set", "").strip()
    parts = [p.strip() for p in text.split("|", 1)]
    if len(parts) < 2:
        await message.answer("Uso: /promo_set <stagione>|<testo>")
        return
    season, text_msg = parts
    seasonal_promos[season] = text_msg
    save_seasonal_promos(seasonal_promos)
    await message.answer("Promo stagionale aggiornata.")


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
    lang_guess = detect_language(message.text or "")
    if lang_guess and message.from_user:
        current = customers_cache.get(str(message.from_user.id), {}).get("lang")
        if not current:
            set_lang(message.from_user.id, lang_guess)
    if message.from_user:
        record = get_customer(message.from_user.id)
        if record.get("stage") == "order_collect" and message.text:
            process_order(message.text, message)
            update_customer(message.from_user.id, {"stage": "idle"})
            return
    if detect_b2b(message.text or "") and message.from_user:
        update_customer(message.from_user.id, {"type": "b2b"})
        await message.answer(
            t(message.from_user.id if message.from_user else None, "b2b_ack")
            + "\n"
            "Se vuoi applicarlo, inviami Partita IVA e nome azienda."
        )
        return
    pref = detect_preference(message.text or "")
    if pref and message.from_user:
        record = customers_cache.get(str(message.from_user.id), {})
        record["preference"] = pref
        customers_cache[str(message.from_user.id)] = record
        save_customers(customers_cache)
    if keyword == "catalogo":
        await cmd_catalogo(message)
        return
    if keyword == "order_quick":
        await message.answer(
            t(message.from_user.id if message.from_user else None, "order_quick")
            + "\n\n"
            + t(message.from_user.id if message.from_user else None, "payment_flow")
        )
        if message.from_user:
            update_customer(message.from_user.id, {"stage": "order_collect"})
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
        await message.answer(t(message.from_user.id if message.from_user else None, "shipping_flow"))
        return
    if keyword == "ordine":
        details = message.text
        if details and ":" in details:
            process_order(details, message)
        else:
            await message.answer(
                t(message.from_user.id if message.from_user else None, "order_template")
                + "\n\n"
                + t(message.from_user.id if message.from_user else None, "shipping_flow")
                + "\n\n"
                + t(message.from_user.id if message.from_user else None, "payment_flow")
            )
            if message.from_user:
                update_customer(message.from_user.id, {"stage": "order_collect"})
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
    if faq_cache:
        text = (message.text or "").lower()
        for key, answer in faq_cache.items():
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
