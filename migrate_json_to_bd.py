import os
import json
import psycopg2
from pathlib import Path

DATABASE_URL = os.environ["DATABASE_URL"]
JSON_PATH = Path("data/products.json")

if not JSON_PATH.exists():
    print("products.json non trovato.")
    exit(1)

with JSON_PATH.open("r", encoding="utf-8") as f:
    products = json.load(f)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

for p in products:
    # Converte stringhe in tipi corretti
    price = float(p.get("price", "0"))
    stock = int(p.get("stock", "0"))
    featured = p.get("featured", "false").lower() == "true"
    is_sample = p.get("is_sample", "false").lower() == "true"

    cur.execute("""
        INSERT INTO products (
            id, name, description, price, image_url, category,
            stock, featured, is_sample, details, translations,
            created_date, updated_date, created_by_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            price = EXCLUDED.price,
            image_url = EXCLUDED.image_url,
            category = EXCLUDED.category,
            stock = EXCLUDED.stock,
            featured = EXCLUDED.featured,
            is_sample = EXCLUDED.is_sample,
            details = EXCLUDED.details,
            translations = EXCLUDED.translations,
            created_date = EXCLUDED.created_date,
            updated_date = EXCLUDED.updated_date,
            created_by_id = EXCLUDED.created_by_id
    """, (
        p.get("id"),
        p.get("name"),
        p.get("description"),
        price,
        p.get("image_url"),
        p.get("category"),
        stock,
        featured,
        is_sample,
        p.get("details"),
        p.get("translations"),
        p.get("created_date"),
        p.get("updated_date"),
        p.get("created_by_id"),
    ))

conn.commit()
cur.close()
conn.close()
print("Dati migrati da products.json a PostgreSQL.")