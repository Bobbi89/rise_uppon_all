from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Product:
    name: str
    description: str
    price: str
    category: str
    featured: str = "false"
    stock: str = ""
