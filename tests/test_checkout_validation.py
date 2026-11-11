import asyncio
from types import SimpleNamespace

import pytest
from aiohttp.test_utils import TestClient, TestServer
from test_payments import BOT_TOKEN, make_init_data
from oro_naturale import api


@pytest.mark.parametrize('items,status', [
    ([{'id': 'p1', 'quantity': 0}], 400),
    ([{'id': 'p1', 'quantity': -1}], 400),
    ([{'id': 'p1', 'quantity': 1.5}], 400),
    ([{'id': 'p1', 'quantity': True}], 400),
    ([{'id': 'p1', 'quantity': 'oops'}], 400),
    ([{'id': 'p1', 'quantity': 4}], 409),
    ([{'id': 'p1', 'quantity': 2}, {'id': 'p1', 'quantity': 2}], 409),
    (['bad'], 400),
    ({'id': 'p1'}, 400),
])
def test_invalid_cart_has_no_side_effects(monkeypatch, items, status):
    def forbidden(*args, **kwargs):
        pytest.fail('invalid checkout touched database or payment provider')
    monkeypatch.setattr(api.db, 'upsert_customer', forbidden)
    monkeypatch.setattr(api, 'build_client', forbidden)
    settings = SimpleNamespace(telegram_bot_token=BOT_TOKEN, admin_chat_ids=set(),
        free_shipping_min=69, default_shipping=10.4, stripe_currency='eur')
    ctx = SimpleNamespace(settings=settings, products=[{'id':'p1', 'name':'Olio', 'price':10, 'stock':3}])
    async def run():
        async with TestClient(TestServer(api.build_api(ctx))) as client:
            response = await client.post('/orders', headers={'X-Init-Data':make_init_data({'id':1})},
                json={'items':items, 'shipping':{'country':'IT'}})
            assert response.status == status
    asyncio.run(run())

@pytest.mark.parametrize('database_ok,frontend_ok,status', [(True,True,200),(False,True,503),(True,False,503)])
def test_readiness(monkeypatch, tmp_path, database_ok, frontend_ok, status):
    from oro_naturale import webserver
    monkeypatch.setattr(webserver, 'WEB_DIST', tmp_path)
    if frontend_ok:
        (tmp_path / 'index.html').write_text('shop')
    def check():
        if not database_ok:
            raise RuntimeError('private connection detail')
        return True
    monkeypatch.setattr(api.db, 'check_ready', check)
    async def run():
        async with TestClient(TestServer(webserver.build_web_app())) as client:
            response = await client.get('/ready')
            assert response.status == status
            assert 'private' not in await response.text()
    asyncio.run(run())

@pytest.mark.parametrize('method,status', [('revolut',503),('paypal',503),('unknown',400)])
def test_disabled_payment_does_not_create_order(monkeypatch, method, status):
    def forbidden(*args, **kwargs):
        pytest.fail('disabled payment touched storage')
    monkeypatch.setattr(api.db, 'upsert_customer', forbidden)
    settings = SimpleNamespace(telegram_bot_token=BOT_TOKEN, admin_chat_ids=set(),
        free_shipping_min=69, default_shipping=10.4, stripe_currency='eur',
        revolut_secret_key='', revolut_public_key='', paypal_email='')
    ctx = SimpleNamespace(settings=settings, products=[{'id':'p1','price':10,'stock':3}])
    async def run():
        async with TestClient(TestServer(api.build_api(ctx))) as client:
            response = await client.post('/orders', headers={'X-Init-Data':make_init_data({'id':1})},
                json={'items':[{'id':'p1','quantity':1}], 'payment_method':method})
            assert response.status == status
    asyncio.run(run())


def test_valid_paypal_checkout_preserves_server_prices(monkeypatch):
    saved = []
    monkeypatch.setattr(api.db, 'upsert_customer', lambda *a, **kw: None)
    monkeypatch.setattr(api.db, 'create_order', lambda order: saved.append(order))
    monkeypatch.setattr(api.db, 'get_order', lambda oid: saved[0])
    settings = SimpleNamespace(telegram_bot_token=BOT_TOKEN, admin_chat_ids=set(),
        free_shipping_min=100, default_shipping=8, stripe_currency='eur',
        paypal_email='shop@example.test', paypal_me='')
    ctx = SimpleNamespace(settings=settings, products=[{'id':'p1','name':'Olio','price':12.95,'stock':3}])
    async def run():
        async with TestClient(TestServer(api.build_api(ctx))) as client:
            response = await client.post('/orders', headers={'X-Init-Data':make_init_data({'id':1})},
                json={'items':[{'id':'p1','quantity':2,'price':0.01}], 'payment_method':'paypal'})
            assert response.status == 200
            result = await response.json()
            assert result['total'] == 33.90
            assert saved[0]['status'] == 'awaiting_payment'
    asyncio.run(run())
