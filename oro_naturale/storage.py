from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

from .models import Product


class FileStore:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def json_path(self, name: str) -> Path:
        return self.data_dir / name

    def load_json(self, name: str, default: Any) -> Any:
        path = self.json_path(name)
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, name: str, data: Any) -> None:
        path = self.json_path(name)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def append_jsonl(self, name: str, payload: dict[str, Any]) -> None:
        path = self.json_path(name)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def tail_jsonl(self, name: str, limit: int = 10) -> list[dict[str, Any]]:
        path = self.json_path(name)
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows[-limit:]


def load_products_from_csv(path: str) -> list[Product]:
    items: list[Product] = []
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
                    featured=row.get("featured", "").strip() or "false",
                    stock=row.get("stock", "").strip(),
                )
            )
    return items


def load_products_json(path: Path) -> list[Product]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    products: list[Product] = []
    for row in raw:
        products.append(
            Product(
                name=str(row.get("name", "")).strip(),
                description=str(row.get("description", "")).strip(),
                price=str(row.get("price", "")).strip(),
                category=str(row.get("category", "")).strip(),
                featured=str(row.get("featured", "false")).strip() or "false",
                stock=str(row.get("stock", "")).strip(),
            )
        )
    return products


def save_products_json(path: Path, products: list[Product]) -> None:
    raw = [
        {
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "category": p.category,
            "featured": p.featured,
            "stock": p.stock,
        }
        for p in products
    ]
    with path.open("w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
