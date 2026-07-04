# ═══════════════════════════════════════════════════════════════════
#  Oro Naturale — Autenticazione Mini App (Telegram initData)
#
#  Telegram firma i dati di sessione della Web App (initData) con HMAC.
#  Validandoli server-side conosciamo con certezza l'utente reale, così
#  ogni utente vede solo i propri ordini e solo gli admin gestiscono il
#  tracking. Riferimento:
#  https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Optional
from urllib.parse import parse_qsl


def validate_init_data(
    init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int = 24 * 3600,
) -> Optional[dict]:
    """
    Verifica la firma HMAC di initData e ne restituisce il payload (dict con
    'user' già decodificato) se valido, altrimenti None.

    Args:
        init_data: la stringa initData grezza (query-string) dalla Web App.
        bot_token: il token del bot (segreto condiviso con Telegram).
        max_age_seconds: rifiuta initData più vecchio di questo (anti-replay).
    """
    if not init_data or not bot_token:
        return None

    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    except ValueError:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    # data_check_string: coppie chiave=valore ordinate, unite da \n
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    # anti-replay opzionale sull'auth_date
    auth_date = pairs.get("auth_date")
    if auth_date and auth_date.isdigit() and max_age_seconds > 0:
        if time.time() - int(auth_date) > max_age_seconds:
            return None

    # decodifica il campo user (JSON)
    if "user" in pairs:
        try:
            pairs["user"] = json.loads(pairs["user"])
        except (json.JSONDecodeError, TypeError):
            pairs["user"] = None

    return pairs


def user_id_from_init_data(init_data: str, bot_token: str) -> Optional[int]:
    """Scorciatoia: restituisce l'id utente Telegram se initData è valido."""
    data = validate_init_data(init_data, bot_token)
    if not data:
        return None
    user = data.get("user") or {}
    uid = user.get("id")
    return int(uid) if isinstance(uid, int) or (isinstance(uid, str) and uid.isdigit()) else None
