# ═══════════════════════════════════════════════════════════════════
#  Oro Naturale — Storage
#  FileStore: gestione JSON su disco
#  load_products_json / save_products_json: serializzazione prodotti
#
#  NOTA: questo modulo NON importa BotContext per evitare
#  il circular import (context → storage → context).
#  BotContext riceve un'istanza di FileStore già costruita.
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  FileStore
# ═══════════════════════════════════════════════════════════════════

class FileStore:
    """
    Wrapper per lettura/scrittura di file JSON in una directory base.

    Uso tipico:
        store = FileStore(Path("/app/data"))
        data  = store.load_json("company.json", default={})
        store.save_json("company.json", data)
        path  = store.json_path("custom_products.json")
    """

    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ── path helper ────────────────────────────────────────────────

    def json_path(self, filename: str) -> Path:
        """Restituisce il Path assoluto per un file nella base_dir."""
        return self.base_dir / filename

    # ── lettura ───────────────────────────────────────────────────

    def load_json(self, filename: str, default: Any = None) -> Any:
        """
        Legge un file JSON dalla base_dir.
        Restituisce `default` se il file non esiste o è corrotto.
        """
        path = self.json_path(filename)
        if not path.exists():
            logger.debug("load_json: %s non trovato, uso default", path)
            return default if default is not None else {}
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("load_json: errore lettura %s — %s", path, exc)
            return default if default is not None else {}

    # ── scrittura ─────────────────────────────────────────────────

    def save_json(self, filename: str, data: Any) -> None:
        """
        Scrive `data` come JSON nella base_dir.
        Crea la directory se non esiste.
        """
        path = self.json_path(filename)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
            logger.debug("save_json: salvato %s", path)
        except OSError as exc:
            logger.error("save_json: errore scrittura %s — %s", path, exc)


# ═══════════════════════════════════════════════════════════════════
#  Prodotti — serializzazione JSON
#  Import locale di Product qui (models → storage, nessun ciclo)
# ═══════════════════════════════════════════════════════════════════

def load_products_json(path: Path | str) -> list:
    """
    Carica una lista di Product da un file JSON.
    Restituisce lista vuota se il file non esiste o è corrotto.

    Importa Product inline per evitare import circolari in fase
    di inizializzazione del package.
    """
    from .models import Product  # import locale — sicuro, models non importa storage

    path = Path(path)
    if not path.exists():
        logger.debug("load_products_json: %s non trovato", path)
        return []
    try:
        with path.open("r", encoding="utf-8") as fh:
            raw: list[dict] = json.load(fh)
        products: list[Product] = []
        for item in raw:
            try:
                products.append(Product(**item))
            except TypeError as exc:
                logger.warning("load_products_json: record ignorato — %s", exc)
        logger.debug("load_products_json: caricati %d prodotti da %s", len(products), path)
        return products
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("load_products_json: errore lettura %s — %s", path, exc)
        return []


def save_products_json(path: Path | str, products: list) -> None:
    """
    Salva una lista di Product in un file JSON.
    Ogni Product viene serializzato con dataclasses.asdict se disponibile,
    altrimenti con __dict__.
    """
    import dataclasses

    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized: list[dict] = []
        for p in products:
            if dataclasses.is_dataclass(p):
                serialized.append(dataclasses.asdict(p))
            elif hasattr(p, "__dict__"):
                serialized.append(p.__dict__)
            else:
                serialized.append(dict(p))
        with path.open("w", encoding="utf-8") as fh:
            json.dump(serialized, fh, ensure_ascii=False, indent=2)
        logger.debug("save_products_json: salvati %d prodotti in %s", len(products), path)
    except OSError as exc:
        logger.error("save_products_json: errore scrittura %s — %s", path, exc)
