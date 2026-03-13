# Oro Naturale Telegram Agent

Telegram bot per promuovere i prodotti Oro Naturale e rispondere a richieste di catalogo, prezzi e ordini.

## Setup rapido

1. Crea un bot con BotFather e inserisci il token in `.env`.
2. Installa le dipendenze:

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

3. Avvia il bot:

```bash
python bot.py
```

## Comandi

- `/catalogo` tutti i prodotti dal CSV
- `/olio` extravergini
- `/aromatizzati` oli aromatizzati
- `/vini` vini e spumanti
- `/cosmetici` cosmetici
- `/gift` confezioni regalo
- `/ordine` richiede i dati per ordine
- `/promo` messaggio promozionale
- `/promo_on <ore>` promo automatiche nella chat
- `/promo_off` stop promo automatiche

## Dati

Il bot legge i prodotti da `Product_export.csv`.

## Deploy su Railway

1. Crea un nuovo progetto su Railway e collega questo repo.
2. Imposta le variabili d'ambiente:
   - `TELEGRAM_BOT_TOKEN`
   - `ADMIN_CHAT_ID` (opzionale)
   - `PRODUCTS_CSV` (opzionale, default `Product_export.csv`)
3. Deploy. Railway avvia automaticamente il comando definito in `nixpacks.toml`.
