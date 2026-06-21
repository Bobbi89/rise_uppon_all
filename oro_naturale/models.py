# models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Product:
    id: str = ""
    name: str = ""
    description: str = ""
    price: str = "0"
    category: str = ""
    image_url: str = ""
    featured: str = "false"
    stock: str = "0"
    details: dict[str, Any] = field(default_factory=dict)