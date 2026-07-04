# ═══════════════════════════════════════════════════════════════════
#  Oro Naturale — Web server della Mini App
#
#  Serve la build statica di web/dist sullo stesso processo del bot.
#  Su Railway il servizio riceve un dominio HTTPS quando ascolta su
#  $PORT: così la Mini App è raggiungibile senza un servizio separato.
#
#  aiohttp è già una dipendenza di aiogram, quindi nessun pacchetto extra.
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web

logger = logging.getLogger(__name__)

# web/dist rispetto alla root del repo (…/oro_naturale/webserver.py → …/web/dist)
WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"


def _index_response() -> web.StreamResponse:
    index = WEB_DIST / "index.html"
    if not index.exists():
        return web.Response(
            text="Mini App non ancora compilata (manca web/dist). "
            "Esegui `npm --prefix web run build`.",
            status=503,
        )
    # no-cache sull'HTML così gli aggiornamenti arrivano subito;
    # gli asset con hash nel nome restano cacheabili a lungo.
    resp = web.FileResponse(index)
    resp.headers["Cache-Control"] = "no-cache"
    return resp


async def _index(_request: web.Request) -> web.StreamResponse:
    return _index_response()


async def _health(_request: web.Request) -> web.StreamResponse:
    return web.json_response({"status": "ok", "dist": WEB_DIST.exists()})


def build_web_app(ctx: object | None = None, bot: object | None = None) -> web.Application:
    app = web.Application()
    app.router.add_get("/", _index)
    app.router.add_get("/health", _health)

    # API della Mini App (ordini, pagamenti Revolut, profilo, admin)
    if ctx is not None:
        from .api import build_api
        app.add_subapp("/api", build_api(ctx, bot))

    assets = WEB_DIST / "assets"
    if assets.exists():
        app.router.add_static("/assets", assets, name="assets")

    # SPA fallback: qualunque altro path serve l'index (la mini app è client-side)
    app.router.add_get("/{tail:.*}", _index)
    return app


async def start_web_server(port: int, ctx: object | None = None, bot: object | None = None) -> web.AppRunner:
    """Avvia il server (static + API) su 0.0.0.0:port e ritorna il runner (per lo shutdown)."""
    runner = web.AppRunner(build_web_app(ctx, bot))
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    if WEB_DIST.exists():
        logger.info("🌐 Mini App servita su :%d (da %s)", port, WEB_DIST)
    else:
        logger.warning("🌐 Web server su :%d ma web/dist non esiste ancora", port)
    return runner
