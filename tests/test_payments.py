# Test per pagamenti Revolut, DB ordini/clienti, auth initData e API.
# I test DB/API si auto-saltano se non c'è un Postgres di test raggiungibile.
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oro_naturale.revolut import RevolutClient, RevolutError, is_paid  # noqa: E402
from oro_naturale.webauth import user_id_from_init_data, validate_init_data  # noqa: E402

BOT_TOKEN = "123456:TESTTOKEN"


def make_init_data(user: dict, bot_token: str = BOT_TOKEN, auth_date: int | None = None) -> str:
    fields = {
        "auth_date": str(auth_date or int(time.time())),
        "user": json.dumps(user, separators=(",", ":")),
    }
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


# ─── initData (sempre) ──────────────────────────────────────────────

def test_init_data_valid():
    idata = make_init_data({"id": 777, "first_name": "Bobbi"})
    data = validate_init_data(idata, BOT_TOKEN)
    assert data and data["user"]["id"] == 777
    assert user_id_from_init_data(idata, BOT_TOKEN) == 777


def test_init_data_wrong_token_rejected():
    idata = make_init_data({"id": 1, "first_name": "X"})
    assert validate_init_data(idata, "999:WRONG") is None


def test_init_data_tampered_rejected():
    idata = make_init_data({"id": 1, "first_name": "Bobbi"})
    assert validate_init_data(idata.replace("Bobbi", "Hacker"), BOT_TOKEN) is None


def test_init_data_expired_rejected():
    idata = make_init_data({"id": 1, "first_name": "X"}, auth_date=int(time.time()) - 100000)
    assert validate_init_data(idata, BOT_TOKEN, max_age_seconds=3600) is None


def test_init_data_empty():
    assert validate_init_data("", BOT_TOKEN) is None
    assert user_id_from_init_data("", BOT_TOKEN) is None


# ─── Revolut client (sempre, con server locale finto) ───────────────

def test_revolut_client_create_and_get():
    from aiohttp import web

    async def run():
        seen = {}

        async def create(request):
            assert request.headers["Authorization"] == "Bearer sk_test"
            seen["body"] = await request.json()
            return web.json_response({"id": "6a1b", "token": "tok_pub", "state": "pending"})

        async def get(request):
            return web.json_response({"id": request.match_info["oid"], "state": "completed"})

        app = web.Application()
        app.router.add_post("/orders", create)
        app.router.add_get("/orders/{oid}", get)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = list(runner.addresses)[0][1]

        client = RevolutClient("sk_test", base_url=f"http://127.0.0.1:{port}")
        order = await client.create_order(amount_minor=3990, currency="EUR", merchant_order_ext_ref="ON-1")
        assert order["token"] == "tok_pub"
        assert seen["body"]["amount"] == 3990 and seen["body"]["merchant_order_ext_ref"] == "ON-1"

        got = await client.get_order("6a1b")
        assert is_paid(got)

        with pytest.raises(RevolutError):
            await client.create_order(amount_minor=0)

        await runner.cleanup()

    asyncio.run(run())


def test_revolut_build_client_none_without_key():
    from oro_naturale.revolut import build_client

    assert build_client("", "sandbox") is None
    assert build_client("sk_x", "sandbox") is not None


def test_config_reads_revolut_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("Revolut_public_api", "pk_123")
    monkeypatch.setenv("revolut_secret_api", "sk_123")
    monkeypatch.setenv("REVOLUT_MODE", "prod")
    from oro_naturale.config import load_settings

    s = load_settings()
    assert s.revolut_public_key == "pk_123"
    assert s.revolut_secret_key == "sk_123"
    assert s.revolut_mode == "prod"


# ─── DB + API (si saltano senza Postgres di test) ───────────────────

TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://postgres@127.0.0.1:55432/oro_test")


def _db_available() -> bool:
    try:
        import psycopg2

        conn = psycopg2.connect(TEST_DB_URL, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="Postgres di test non disponibile")


@pytest.fixture()
def clean_db():
    import psycopg2

    from oro_naturale import db as dbmod

    dbmod.init_schema(TEST_DB_URL)
    conn = psycopg2.connect(TEST_DB_URL)
    cur = conn.cursor()
    cur.execute("TRUNCATE orders, customers;")
    conn.commit()
    conn.close()
    return TEST_DB_URL


@requires_db
def test_db_order_lifecycle(clean_db):
    from oro_naturale import db as dbmod

    dbmod.upsert_customer(1, username="bob", first_name="Bobbi", database_url=clean_db)
    dbmod.upsert_customer(1, phone="+39", city="Perugia", database_url=clean_db)
    c = dbmod.get_customer(1, database_url=clean_db)
    assert c["first_name"] == "Bobbi" and c["city"] == "Perugia"

    dbmod.create_order({
        "id": "ON-X", "user_id": 1, "username": "bob",
        "items": [{"id": "p1", "name": "Olio", "price": 10.0, "quantity": 2}],
        "subtotal": 20.0, "shipping": 14, "total": 34.0, "status": "pending",
    }, database_url=clean_db)
    o = dbmod.get_order("ON-X", database_url=clean_db)
    assert o["total"] == 34.0 and o["items"][0]["quantity"] == 2

    dbmod.update_order_status("ON-X", "paid", mark_paid=True, payment_method="apple_pay", database_url=clean_db)
    o = dbmod.get_order("ON-X", database_url=clean_db)
    assert o["status"] == "paid" and o["paid_at"] and o["payment_method"] == "apple_pay"

    dbmod.set_tracking("ON-X", carrier="BRT", code="T1", url="https://x", database_url=clean_db)
    o = dbmod.get_order("ON-X", database_url=clean_db)
    assert o["tracking_code"] == "T1" and o["status"] == "shipped"

    assert len(dbmod.list_user_orders(1, database_url=clean_db)) == 1
    assert dbmod.list_user_orders(999, database_url=clean_db) == []


@requires_db
def test_api_full_flow(clean_db, monkeypatch):
    from aiohttp import web
    from aiohttp.test_utils import TestClient, TestServer

    import oro_naturale.api as api
    from oro_naturale.revolut import RevolutClient

    monkeypatch.setenv("DATABASE_URL", clean_db)

    async def run():
        rev_state = {"state": "pending", "ext": None}

        async def rc(request):
            b = await request.json()
            return web.json_response({"id": "rev-" + b["merchant_order_ext_ref"], "token": "tok",
                                      "state": "pending", "merchant_order_ext_ref": b["merchant_order_ext_ref"]})

        async def rg(request):
            return web.json_response({"id": request.match_info["oid"], "state": rev_state["state"]})

        revapp = web.Application()
        revapp.router.add_post("/orders", rc)
        revapp.router.add_get("/orders/{oid}", rg)
        revrunner = web.AppRunner(revapp)
        await revrunner.setup()
        revsite = web.TCPSite(revrunner, "127.0.0.1", 0)
        await revsite.start()
        revport = list(revrunner.addresses)[0][1]

        monkeypatch.setattr(
            api, "build_client",
            lambda sk, mode, ver=None: RevolutClient(sk, base_url=f"http://127.0.0.1:{revport}") if sk else None,
        )

        notifs = []

        class FakeBot:
            async def send_message(self, cid, text, **kw):
                notifs.append((cid, text))

        settings = SimpleNamespace(
            telegram_bot_token=BOT_TOKEN, admin_chat_ids={42},
            revolut_public_key="pk", revolut_secret_key="sk", revolut_mode="sandbox",
            revolut_api_version="2024-09-01", stripe_currency="eur",
            free_shipping_min=100.0, default_shipping=14.0,
        )
        ctx = SimpleNamespace(settings=settings, products=[
            {"id": "p1", "name": "Olio", "price": 12.95, "stock": 100},
        ])

        client = TestClient(TestServer(api.build_api(ctx, FakeBot())))
        await client.start_server()
        H = {"X-Init-Data": make_init_data({"id": 5001, "first_name": "Bobbi", "username": "bob"})}
        AH = {"X-Init-Data": make_init_data({"id": 42, "first_name": "Admin"})}

        # crea ordine (2×12.95 + 14 = 39.90)
        r = await client.post("/orders", headers=H, json={
            "items": [{"id": "p1", "quantity": 2}],
            "shipping": {"name": "Bobbi", "phone": "+39", "address": "Via Roma 1", "city": "Perugia", "zip": "06100"},
        })
        o = await r.json()
        assert r.status == 200 and o["total"] == 39.90 and o["revolut_token"] == "tok"
        oid = o["order_id"]

        # prezzo client ignorato
        r = await client.post("/orders", headers=H, json={"items": [{"id": "p1", "quantity": 1, "price": 0.01}], "shipping": {}})
        assert (await r.json())["subtotal"] == 12.95

        # senza auth -> 401
        r = await client.post("/orders", json={"items": [{"id": "p1", "quantity": 1}]})
        assert r.status == 401

        # confirm non pagato
        r = await client.post(f"/orders/{oid}/confirm", headers=H, json={})
        assert (await r.json())["paid"] is False

        # confirm pagato + notifica admin
        rev_state["state"] = "completed"
        r = await client.post(f"/orders/{oid}/confirm", headers=H, json={"payment_method": "apple_pay"})
        body = await r.json()
        assert body["paid"] is True and body["order"]["status"] == "paid"
        assert any(cid == 42 and "NUOVO ORDINE" in t for cid, t in notifs)

        # profilo utente
        r = await client.get("/profile", headers=H)
        p = await r.json()
        assert any(x["id"] == oid for x in p["orders"]) and p["customer"]["city"] == "Perugia"

        # isolamento: altro utente non vede l'ordine
        r = await client.get("/profile", headers={"X-Init-Data": make_init_data({"id": 9, "first_name": "Z"})})
        assert all(x["id"] != oid for x in (await r.json())["orders"])

        # admin vede tutto; non-admin 403
        r = await client.get("/admin/orders", headers=AH)
        assert any(x["id"] == oid for x in (await r.json())["orders"])
        r = await client.get("/admin/orders", headers=H)
        assert r.status == 403

        # admin set tracking -> notifica utente
        notifs.clear()
        r = await client.post(f"/admin/orders/{oid}/tracking", headers=AH,
                              json={"carrier": "BRT", "code": "T9", "url": "https://brt.it/T9"})
        t = await r.json()
        assert t["order"]["tracking_code"] == "T9" and t["order"]["status"] == "shipped"
        assert any(cid == 5001 and "spedito" in txt for cid, txt in notifs)
        r = await client.post(f"/admin/orders/{oid}/tracking", headers=H, json={"carrier": "X", "code": "Y"})
        assert r.status == 403

        await client.close()
        await revrunner.cleanup()

    asyncio.run(run())


@requires_db
def test_api_paypal_and_shipping(clean_db, monkeypatch):
    """Checkout PayPal (ordine 'awaiting_payment' + istruzioni) e spedizione a fasce."""
    from aiohttp.test_utils import TestClient, TestServer

    import oro_naturale.api as api

    monkeypatch.setenv("DATABASE_URL", clean_db)
    # Revolut disattivato: create_order non deve dipendere da esso per PayPal.
    monkeypatch.setattr(api, "build_client", lambda sk, mode, ver=None: None)

    async def run():
        notifs = []

        class FakeBot:
            async def send_message(self, cid, text, **kw):
                notifs.append((cid, text))

        settings = SimpleNamespace(
            telegram_bot_token=BOT_TOKEN, admin_chat_ids={42},
            revolut_public_key="", revolut_secret_key="", revolut_mode="sandbox",
            revolut_api_version="2024-09-01", stripe_currency="eur",
            free_shipping_min=69.0, default_shipping=10.40,
            paypal_email="shop@example.com", paypal_me="paypal.me/shop",
        )
        ctx = SimpleNamespace(settings=settings, products=[
            {"id": "p1", "name": "Olio", "price": 12.95, "stock": 100},
        ])

        client = TestClient(TestServer(api.build_api(ctx, FakeBot())))
        await client.start_server()
        H = {"X-Init-Data": make_init_data({"id": 6001, "first_name": "Bobbi", "username": "bob"})}
        AH = {"X-Init-Data": make_init_data({"id": 42, "first_name": "Admin"})}

        # Ordine PayPal, Italia: 2×12.95=25.90 + 10.40 spedizione = 36.30
        r = await client.post("/orders", headers=H, json={
            "payment_method": "paypal",
            "items": [{"id": "p1", "quantity": 2}],
            "shipping": {"name": "Bobbi", "phone": "+39", "address": "Via Roma 1",
                         "city": "Perugia", "zip": "06100", "country": "IT"},
        })
        o = await r.json()
        assert r.status == 200
        assert o["payment_method"] == "paypal"
        assert o["subtotal"] == 25.90 and o["shipping"] == 10.40 and o["total"] == 36.30
        assert o["paypal_email"] == "shop@example.com"
        assert o["paypal_link"] == "https://paypal.me/shop/36.30EUR"
        paypal_oid = o["order_id"]
        # notifica admin "da confermare"
        assert any(cid == 42 and "CONFERMARE" in txt for cid, txt in notifs)

        # L'ordine è visibile all'admin come awaiting_payment
        r = await client.get("/admin/orders", headers=AH)
        admin_orders = (await r.json())["orders"]
        row = next(x for x in admin_orders if x["id"] == paypal_oid)
        assert row["status"] == "awaiting_payment"
        assert row["items"][0]["quantity"] == 2  # l'admin vede cosa è stato ordinato

        # "Segna pagato"
        r = await client.post(f"/admin/orders/{paypal_oid}/status", headers=AH, json={"status": "paid"})
        assert (await r.json())["order"]["status"] == "paid"

        # Spedizione per paese: nordico 14€, extra-UE 25€, sopra soglia gratis
        async def total_for(country, qty):
            rr = await client.post("/orders", headers=H, json={
                "payment_method": "paypal",
                "items": [{"id": "p1", "quantity": qty}],
                "shipping": {"country": country},
            })
            return await rr.json()

        se = await total_for("SE", 2)   # 25.90 + 14 = 39.90
        assert se["shipping"] == 14.0 and se["total"] == 39.90
        us = await total_for("US", 2)   # 25.90 + 25 = 50.90
        assert us["shipping"] == 25.0 and us["total"] == 50.90
        free = await total_for("IT", 6)  # 77.70 >= 69 -> gratis
        assert free["shipping"] == 0.0 and free["total"] == 77.70

        await client.close()

    asyncio.run(run())


@requires_db
def test_api_admin_set_status(clean_db, monkeypatch):
    from aiohttp.test_utils import TestClient, TestServer

    import oro_naturale.api as api
    from oro_naturale import db as dbmod

    monkeypatch.setenv("DATABASE_URL", clean_db)
    monkeypatch.setattr(api, "build_client", lambda sk, mode, ver=None: None)

    # ordine già presente
    dbmod.create_order({
        "id": "ON-ST", "user_id": 7001, "username": "mario",
        "items": [{"id": "p1", "name": "Olio", "price": 10.0, "quantity": 1}],
        "subtotal": 10.0, "shipping": 0, "total": 10.0, "status": "paid",
    }, database_url=clean_db)

    async def run():
        notifs = []

        class FakeBot:
            async def send_message(self, cid, text, **kw):
                notifs.append((cid, text))

        settings = SimpleNamespace(
            telegram_bot_token=BOT_TOKEN, admin_chat_ids={42},
            revolut_public_key="", revolut_secret_key="", revolut_mode="sandbox",
            revolut_api_version="x", stripe_currency="eur",
            free_shipping_min=100.0, default_shipping=14.0,
        )
        ctx = SimpleNamespace(settings=settings, products=[])
        client = TestClient(TestServer(api.build_api(ctx, FakeBot())))
        await client.start_server()
        AH = {"X-Init-Data": make_init_data({"id": 42, "first_name": "Admin"})}
        H = {"X-Init-Data": make_init_data({"id": 7001, "first_name": "Mario"})}

        # admin segna "in preparazione" -> notifica utente
        r = await client.post("/admin/orders/ON-ST/status", headers=AH, json={"status": "preparing"})
        assert (await r.json())["order"]["status"] == "preparing"
        assert any(cid == 7001 for cid, _ in notifs)

        # stato non valido -> 400
        r = await client.post("/admin/orders/ON-ST/status", headers=AH, json={"status": "boh"})
        assert r.status == 400

        # non-admin -> 403
        r = await client.post("/admin/orders/ON-ST/status", headers=H, json={"status": "delivered"})
        assert r.status == 403

        await client.close()

    asyncio.run(run())


@requires_db
def test_admin_excludes_pending_and_clear_pending(clean_db):
    from oro_naturale import db as dbmod

    # 2 ordini utente 1: uno pending, uno pagato
    dbmod.create_order({"id": "ON-P1", "user_id": 1, "items": [], "total": 10, "status": "pending"}, database_url=clean_db)
    dbmod.create_order({"id": "ON-PAID", "user_id": 1, "items": [], "total": 20, "status": "paid"}, database_url=clean_db)
    # ordine pending di un altro utente
    dbmod.create_order({"id": "ON-P2", "user_id": 2, "items": [], "total": 5, "status": "pending"}, database_url=clean_db)

    # admin vede solo i pagati
    admin = dbmod.list_all_orders(database_url=clean_db)
    ids = {o["id"] for o in admin}
    assert "ON-PAID" in ids and "ON-P1" not in ids and "ON-P2" not in ids
    # con exclude_pending=False li vede tutti
    assert len(dbmod.list_all_orders(exclude_pending=False, database_url=clean_db)) == 3

    # l'utente 1 vede entrambi i suoi (pending + pagato)
    assert len(dbmod.list_user_orders(1, database_url=clean_db)) == 2

    # svuota i pending dell'utente 1: resta solo il pagato; l'altro utente non è toccato
    removed = dbmod.delete_pending_orders(1, database_url=clean_db)
    assert removed == 1
    remaining = {o["id"] for o in dbmod.list_user_orders(1, database_url=clean_db)}
    assert remaining == {"ON-PAID"}
    assert len(dbmod.list_user_orders(2, database_url=clean_db)) == 1  # ON-P2 intatto


@requires_db
def test_api_clear_pending_endpoint(clean_db, monkeypatch):
    from aiohttp.test_utils import TestClient, TestServer
    import oro_naturale.api as api
    from oro_naturale import db as dbmod

    monkeypatch.setenv("DATABASE_URL", clean_db)
    monkeypatch.setattr(api, "build_client", lambda sk, mode, ver=None: None)

    dbmod.create_order({"id": "ON-UP", "user_id": 55, "items": [], "total": 9, "status": "pending"}, database_url=clean_db)
    dbmod.create_order({"id": "ON-OK", "user_id": 55, "items": [], "total": 9, "status": "paid"}, database_url=clean_db)

    async def run():
        settings = SimpleNamespace(
            telegram_bot_token=BOT_TOKEN, admin_chat_ids={42}, revolut_public_key="",
            revolut_secret_key="", revolut_mode="sandbox", revolut_api_version="x",
            stripe_currency="eur", free_shipping_min=100.0, default_shipping=14.0,
        )
        ctx = SimpleNamespace(settings=settings, products=[])
        client = TestClient(TestServer(api.build_api(ctx, None)))
        await client.start_server()
        H = {"X-Init-Data": make_init_data({"id": 55, "first_name": "U"})}

        # profilo mostra pending + pagato
        r = await client.get("/profile", headers=H)
        assert len((await r.json())["orders"]) == 2

        # svuota non pagati
        r = await client.post("/profile/clear-pending", headers=H, json={})
        body = await r.json()
        assert body["removed"] == 1 and [o["id"] for o in body["orders"]] == ["ON-OK"]

        # senza auth -> 401
        r = await client.post("/profile/clear-pending", json={})
        assert r.status == 401

        await client.close()

    asyncio.run(run())


# ─── Spedizioni a fasce (come biomarketshop.com) ────────────────────

def test_compute_shipping_tiers():
    from oro_naturale.api import _compute_shipping

    settings = SimpleNamespace(free_shipping_min=69.0, default_shipping=10.40)

    # Sopra soglia: sempre gratis (a prescindere dal paese)
    assert _compute_shipping(69.0, "IT", settings) == 0.0
    assert _compute_shipping(120.0, "US", settings) == 0.0
    # Italia / Europa: tariffa standard
    assert _compute_shipping(50.0, "IT", settings) == 10.40
    assert _compute_shipping(50.0, "de", settings) == 10.40  # case-insensitive
    # Paesi nordici: 14€
    assert _compute_shipping(50.0, "SE", settings) == 14.0
    assert _compute_shipping(50.0, "NO", settings) == 14.0
    # Resto del mondo: 25€
    assert _compute_shipping(50.0, "US", settings) == 25.0
    # Paese assente -> default Italia
    assert _compute_shipping(50.0, "", settings) == 10.40


# ─── Concorrenza: ID ordine univoci ─────────────────────────────────

def test_order_id_unique_under_rapid_calls():
    """Molti ordini creati in rapida successione devono avere ID distinti."""
    from oro_naturale.api import _order_id

    ids = [_order_id() for _ in range(20000)]
    assert len(set(ids)) == len(ids), "collisione di ID ordine"
    assert all(i.startswith("ON-") for i in ids)


@requires_db
def test_api_concurrent_checkout(clean_db, monkeypatch):
    """Più utenti che acquistano nello stesso momento: nessuna collisione,
    ogni ordine è salvato e isolato per utente."""
    from aiohttp.test_utils import TestClient, TestServer

    import oro_naturale.api as api
    from oro_naturale import db as dbmod

    monkeypatch.setenv("DATABASE_URL", clean_db)
    monkeypatch.setattr(api, "build_client", lambda sk, mode, ver=None: None)

    async def run():
        class FakeBot:
            async def send_message(self, cid, text, **kw):
                pass

        settings = SimpleNamespace(
            telegram_bot_token=BOT_TOKEN, admin_chat_ids={42},
            revolut_public_key="", revolut_secret_key="", revolut_mode="sandbox",
            revolut_api_version="2024-09-01", stripe_currency="eur",
            free_shipping_min=69.0, default_shipping=10.40,
            paypal_email="shop@example.com", paypal_me="",
        )
        ctx = SimpleNamespace(settings=settings, products=[
            {"id": "p1", "name": "Olio", "price": 12.95, "stock": 1000},
        ])

        client = TestClient(TestServer(api.build_api(ctx, FakeBot())))
        await client.start_server()

        N = 30  # 30 utenti diversi che ordinano simultaneamente

        async def buy(uid: int):
            H = {"X-Init-Data": make_init_data({"id": uid, "first_name": f"U{uid}"})}
            r = await client.post("/orders", headers=H, json={
                "payment_method": "paypal",
                "items": [{"id": "p1", "quantity": (uid % 3) + 1}],
                "shipping": {"name": f"U{uid}", "phone": "+39", "address": "Via 1",
                             "city": "Perugia", "zip": "06100", "country": "IT"},
            })
            assert r.status == 200, f"utente {uid} ha ricevuto {r.status}"
            return (await r.json())["order_id"]

        # Esecuzione concorrente
        oids = await asyncio.gather(*[buy(1000 + i) for i in range(N)])

        # Tutti gli ID sono unici e tutti gli ordini sono nel DB
        assert len(set(oids)) == N, "ID ordine duplicati sotto carico concorrente"
        for i in range(N):
            orders = await asyncio.to_thread(dbmod.list_user_orders, 1000 + i, database_url=clean_db)
            assert len(orders) == 1, f"utente {1000+i} dovrebbe avere 1 ordine"
            assert orders[0]["id"] in oids

        # L'admin vede tutti e 30 gli ordini
        AH = {"X-Init-Data": make_init_data({"id": 42, "first_name": "Admin"})}
        r = await client.get("/admin/orders", headers=AH)
        admin_ids = {o["id"] for o in (await r.json())["orders"]}
        assert set(oids) <= admin_ids

        await client.close()

    asyncio.run(run())
