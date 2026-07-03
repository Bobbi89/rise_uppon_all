import os
import sys
import time
import psycopg2

# Ritarda l'esecuzione di 3 secondi per dare tempo a Railway 
# di rendere disponibili le variabili d'ambiente
time.sleep(3)

try:
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    if not DATABASE_URL:
        print("ERRORE: La variabile DATABASE_URL non è trovata!")
        sys.exit(1)

    print("Tentativo di connessione al database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("Creazione tabella products...")
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
    print("SUCCESSO: Tabella products creata/verificata.")

except Exception as e:
    print(f"ERRORE CRITICO IN MIGRATE.PY: {type(e).__name__} - {e}")
    # Esci con codice 1 così railway sa che c'è stato un errore
    sys.exit(1)