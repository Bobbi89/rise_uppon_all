# models.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Product:
    name: str
    description: str
    price: str  # Tenuto come stringa per sicurezza durante l'import CSV
    category: str = ""
    image_url: str = ""
    featured: str = "false"
    stock: str = "0"
    details: dict[str, Any] = field(default_factory=dict)