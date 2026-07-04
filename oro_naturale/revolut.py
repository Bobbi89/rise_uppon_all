# ═══════════════════════════════════════════════════════════════════
#  Oro Naturale — Revolut Merchant API client
#
#  Flusso pagamento:
#   1) server crea un ordine Revolut (chiave SEGRETA) → riceve token pubblico
#   2) la Mini App inizializza RevolutCheckout(token) con la chiave PUBBLICA
#      e mostra carta / Revolut Pay / Apple Pay
#   3) a pagamento fatto, il server verifica lo stato dell'ordine e conferma
#
#  Docs: https://developer.revolut.com/docs/merchant/merchant-api
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)

# Versione API Merchant (data). Aggiornabile via env REVOLUT_API_VERSION.
DEFAULT_API_VERSION = "2024-09-01"

_BASE_URLS = {
    "prod": "https://merchant.revolut.com/api",
    "sandbox": "https://sandbox-merchant.revolut.com/api",
}


class RevolutError(RuntimeError):
    """Errore restituito dall'API Revolut o di rete."""


class RevolutClient:
    def __init__(
        self,
        secret_key: str,
        *,
        mode: str = "sandbox",
        api_version: str = DEFAULT_API_VERSION,
        base_url: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        if not secret_key:
            raise RevolutError("Revolut secret key mancante")
        self.secret_key = secret_key
        self.mode = "prod" if mode == "prod" else "sandbox"
        self.api_version = api_version
        self.base_url = (base_url or _BASE_URLS[self.mode]).rstrip("/")
        self.timeout = timeout

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Revolut-Api-Version": self.api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(method, url, json=payload, headers=self._headers) as resp:
                    text = await resp.text()
                    if resp.status >= 400:
                        logger.warning("Revolut %s %s -> %s: %s", method, path, resp.status, text[:300])
                        raise RevolutError(f"Revolut {resp.status}: {text[:200]}")
                    return await resp.json() if text else {}
        except aiohttp.ClientError as exc:
            raise RevolutError(f"Errore di rete Revolut: {exc}") from exc

    async def create_order(
        self,
        *,
        amount_minor: int,
        currency: str = "EUR",
        merchant_order_ext_ref: str | None = None,
        description: str | None = None,
        customer_email: str | None = None,
    ) -> dict:
        """
        Crea un ordine Revolut. `amount_minor` in centesimi (es. 3990 = €39,90).
        Ritorna il dict Revolut con almeno: id, token, state, checkout_url.
        """
        if amount_minor <= 0:
            raise RevolutError("Importo non valido")
        payload: dict[str, Any] = {"amount": amount_minor, "currency": currency}
        if merchant_order_ext_ref:
            payload["merchant_order_ext_ref"] = merchant_order_ext_ref
        if description:
            payload["description"] = description
        if customer_email:
            payload["customer"] = {"email": customer_email}
        return await self._request("POST", "/orders", payload)

    async def get_order(self, order_id: str) -> dict:
        """Recupera lo stato di un ordine Revolut (per confermare il pagamento)."""
        return await self._request("GET", f"/orders/{order_id}")


# Stati Revolut che consideriamo "pagato"
PAID_STATES = {"completed", "authorised", "authorized"}


def is_paid(order: dict) -> bool:
    return str(order.get("state", "")).lower() in PAID_STATES


def build_client(
    secret_key: str,
    mode: str,
    api_version: str = DEFAULT_API_VERSION,
) -> Optional[RevolutClient]:
    """Costruisce il client se la chiave è presente, altrimenti None."""
    if not secret_key:
        return None
    return RevolutClient(secret_key, mode=mode, api_version=api_version)
