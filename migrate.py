import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        image_url TEXT,
        category TEXT,
        stock INTEGER DEFAULT 0,
        featured BOOLEAN DEFAULT FALSE,
        is_sample BOOLEAN DEFAULT FALSE,
        details JSONB,
        translations JSONB,
        created_date TIMESTAMPTZ,
        updated_date TIMESTAMPTZ,
        created_by_id TEXT
    )
""")
conn.commit()
cur.close()
conn.close()
print("Tabella products creata/verificata.")