# Test di regressione per la logica del bot (senza Telegram né DB).
# Esecuzione:  pip install pytest && python -m pytest tests/ -v
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DATABASE_URL", "")  # nessun DB nei test

from oro_naturale.catalog import (  # noqa: E402
    calculate_cart_total,
    category_label,
    find_products,
    product_key,
    product_price_value,
)
from oro_naturale.keyboards import (  # noqa: E402
    BTN_WEBAPP,
    main_menu,
    payment_menu,
    quantity_menu,
    product_card_menu,
    shipping_menu,
    welcome_menu,
)
from oro_naturale.models import Product  # noqa: E402
from oro_naturale.services import (  # noqa: E402
    detect_b2b,
    detect_language,
    parse_country,
    parse_total,
    recommend_upsell,
    shipping_cost,
)
from oro_naturale.storage import FileStore, load_products_from_db  # noqa: E402


def make_product(name="Olio EVO 500ml", price=19.95, category="extra_virgin_olive_oil", stock=10):
    return Product(
        id=f"test-{name}",
        name=name,
        description="descrizione",
        price=price,
        image_url="",
        category=category,
        stock=stock,
    )


class FakeSettings:
    free_shipping_min = 100.0
    default_shipping = 14.0
    b2b_discount = 15.0
    admin_chat_ids = {42}
    stripe_secret_key = ""
    stripe_currency = "eur"


# ─── storage ─────────────────────────────────────────────────────────

def test_filestore_json_roundtrip(tmp_path):
    store = FileStore(tmp_path)
    store.save_json("x.json", {"a": 1})
    assert store.load_json("x.json") == {"a": 1}
    assert store.load_json("missing.json", {"d": True}) == {"d": True}


def test_filestore_append_and_tail_jsonl(tmp_path):
    store = FileStore(tmp_path)
    assert store.tail_jsonl("orders.jsonl", 5) == []
    for i in range(7):
        store.append_jsonl("orders.jsonl", {"order_id": f"ON{i}", "total": i * 10})
    items = store.tail_jsonl("orders.jsonl", 5)
    assert len(items) == 5
    assert items[0]["order_id"] == "ON2"
    assert items[-1]["order_id"] == "ON6"


def test_tail_jsonl_skips_corrupt_lines(tmp_path):
    store = FileStore(tmp_path)
    store.append_jsonl("p.jsonl", {"ok": 1})
    (tmp_path / "p.jsonl").open("a").write("{{{riga rotta\n")
    store.append_jsonl("p.jsonl", {"ok": 2})
    items = store.tail_jsonl("p.jsonl", 10)
    assert [i["ok"] for i in items] == [1, 2]


def test_load_products_from_db_without_database_url():
    assert load_products_from_db() == []


# ─── services ────────────────────────────────────────────────────────

def test_parse_total_with_totale_keyword():
    assert parse_total("totale 45,90") == 45.9
    assert parse_total("Total: 99.95") == 99.95


def test_parse_total_with_currency_suffix():
    # Regressione: prima restituiva 0.5 per "25,50 EUR" e crashava su "30 eur"
    assert parse_total("25,50 EUR") == 25.5
    assert parse_total("30 eur") == 30.0
    assert parse_total("12€") == 12.0


def test_parse_total_no_match():
    assert parse_total("ciao come va") is None


def test_parse_country_and_shipping_cost():
    assert parse_country("paese: DE") == "DE"
    assert parse_country("ordino per l'ITALIA") == "IT"
    settings = FakeSettings()
    assert shipping_cost("IT", 150, settings, {}) == 0.0            # sopra soglia
    assert shipping_cost("IT", 50, settings, {}) == 14.0            # default
    assert shipping_cost("DE", 50, settings, {"DE": 9.5}) == 9.5    # regola dedicata


def test_detect_language_and_b2b():
    assert detect_language("vorrei fare un ordine") == "it"
    assert detect_language("I want to order") == "en"
    assert detect_b2b("ho la partita iva") is True
    assert detect_b2b("sono un privato") is False


def test_recommend_upsell_only_below_gap():
    settings = FakeSettings()
    products = [make_product("A", 5.0), make_product("B", 90.0), make_product("C", 200.0)]
    picks = recommend_upsell(products, subtotal=95.0, settings=settings)
    # gap = 5 → propone solo prodotti con prezzo <= gap+5
    assert [p.name for p in picks] == ["A"]
    assert recommend_upsell(products, subtotal=150.0, settings=settings) == []


# ─── catalog ─────────────────────────────────────────────────────────

def test_product_price_value_handles_strings_and_commas():
    assert product_price_value(make_product(price=12.5)) == 12.5
    assert product_price_value(make_product(price="19,95")) == 19.95
    assert product_price_value(make_product(price="")) is None


def test_calculate_cart_total():
    p1, p2 = make_product("A", 10.0), make_product("B", 5.5)
    cart = {product_key(p1): 2, product_key(p2): 1, "chiave-orfana": 3}
    assert calculate_cart_total([p1, p2], cart) == 25.5


def test_find_products_case_insensitive():
    products = [make_product("Olio ORO 250ml"), make_product("Vino Rosso")]
    assert len(find_products(products, "oro")) == 1
    assert find_products(products, "") == []


def test_category_label_known_and_fallback():
    assert category_label("wines") == "Vini"
    assert category_label("new_stuff") == "New Stuff"


# ─── keyboards ───────────────────────────────────────────────────────

def test_main_menu_webapp_button_only_with_url():
    with_url = main_menu(3, "https://shop.example")
    assert with_url.keyboard[0][0].text == BTN_WEBAPP
    assert with_url.keyboard[0][0].web_app.url == "https://shop.example"
    without = main_menu(3)
    assert without.keyboard[0][0].text != BTN_WEBAPP


def test_welcome_menu_webapp_button_only_with_url():
    with_url = welcome_menu("https://shop.example")
    assert with_url.inline_keyboard[0][0].web_app.url == "https://shop.example"
    without = welcome_menu()
    assert without.inline_keyboard[0][0].web_app is None


def test_shipping_menu_label_uses_configured_cost():
    kb = shipping_menu(14.0)
    assert "€14.00" in kb.inline_keyboard[0][0].text
    assert kb.inline_keyboard[0][0].callback_data == "ship:home"


def test_quantity_menu_callbacks():
    kb = quantity_menu("abc", 1)
    flat = [b.callback_data for row in kb.inline_keyboard for b in row]
    assert "qty:abc:0" in flat          # 🗑️ a qty=1
    assert "qty:abc:2" in flat          # ➕
    assert "add:abc:1" in flat
    kb3 = quantity_menu("abc", 3)
    flat3 = [b.callback_data for row in kb3.inline_keyboard for b in row]
    assert "qty:abc:2" in flat3         # ➖


def test_product_card_menu_out_of_stock():
    kb = product_card_menu("abc", "wines", stock=0)
    assert kb.inline_keyboard[0][0].callback_data == "noop"
    kb_ok = product_card_menu("abc", "wines", stock=5)
    assert kb_ok.inline_keyboard[0][0].callback_data == "add:abc:1"


def test_payment_menu_totals_in_labels():
    kb = payment_menu(26.95)
    assert "€26.95" in kb.inline_keyboard[0][0].text
    assert kb.inline_keyboard[0][0].callback_data == "pay:card"


# ─── models ──────────────────────────────────────────────────────────

def test_product_requires_id():
    import pytest
    with pytest.raises(TypeError):
        Product(name="X", description="d", price=1.0, image_url="", category="wines")  # type: ignore[call-arg]


# ─── Mini App: handler web_app_data ─────────────────────────────────

def test_webapp_order_handler(tmp_path, monkeypatch):
    """L'ordine dalla Mini App viene salvato, confermato e notificato agli admin."""
    import asyncio
    import json
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    import oro_naturale.routers.public as pub
    from oro_naturale.context import BotContext

    settings = SimpleNamespace(
        webapp_url="https://shop.example",
        admin_chat_ids={42},
        default_shipping=14.0,
        free_shipping_min=100.0,
        b2b_discount=15.0,
        followup_hours=24.0,
        stripe_secret_key="",
        stripe_currency="eur",
    )
    store = FileStore(tmp_path)
    ctx = BotContext(settings=settings, store=store)  # type: ignore[arg-type]

    sends: list[str] = []

    async def fake_send(target, text, **kwargs):
        sends.append(text)

    monkeypatch.setattr(pub, "safe_send_message", fake_send)

    router = pub.build_public_router(ctx)
    handler = next(
        h.callback for h in router.message.handlers if h.callback.__name__ == "webapp_order"
    )

    payload = {
        "type": "order",
        "order_id": "ON-12345",
        "total": 39.9,
        "shipping": 14,
        "payment_method": "revolut",
        "customer": {"name": "Bobbi", "phone": "+39", "address": "Via Roma 1", "city": "Perugia", "zip": "06100"},
        "items": [{"id": "x", "name": "Olio ORO", "price": 12.95, "quantity": 2}],
    }
    bot = SimpleNamespace(send_message=AsyncMock())
    message = SimpleNamespace(
        web_app_data=SimpleNamespace(data=json.dumps(payload)),
        from_user=SimpleNamespace(id=7, username="bobbi89"),
        chat=SimpleNamespace(id=7),
        bot=bot,
    )

    asyncio.run(handler(message))

    # Ordine persistito su orders.jsonl
    orders = store.tail_jsonl("orders.jsonl", 5)
    assert len(orders) == 1
    assert orders[0]["order_id"] == "ON-12345"
    assert orders[0]["source"] == "miniapp"
    assert orders[0]["total"] == 39.9

    # Cliente aggiornato a payment_pending
    customers = store.load_json("customers.json", {})
    assert customers["7"]["stage"] == "payment_pending"

    # Conferma inviata all'utente e notifica all'admin
    assert any("Ordine ricevuto" in s for s in sends)
    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.args[0] == 42


def test_webapp_order_handler_invalid_json(tmp_path, monkeypatch):
    """JSON corrotto dalla Mini App: risposta di errore, nessun ordine salvato."""
    import asyncio
    from types import SimpleNamespace

    import oro_naturale.routers.public as pub
    from oro_naturale.context import BotContext

    settings = SimpleNamespace(webapp_url="", admin_chat_ids=set())
    store = FileStore(tmp_path)
    ctx = BotContext(settings=settings, store=store)  # type: ignore[arg-type]

    sends: list[str] = []

    async def fake_send(target, text, **kwargs):
        sends.append(text)

    monkeypatch.setattr(pub, "safe_send_message", fake_send)

    router = pub.build_public_router(ctx)
    handler = next(
        h.callback for h in router.message.handlers if h.callback.__name__ == "webapp_order"
    )
    message = SimpleNamespace(
        web_app_data=SimpleNamespace(data="{{{non-json"),
        from_user=SimpleNamespace(id=7, username=None),
        chat=SimpleNamespace(id=7),
        bot=SimpleNamespace(),
    )
    asyncio.run(handler(message))

    assert store.tail_jsonl("orders.jsonl", 5) == []
    assert any("non validi" in s for s in sends)
