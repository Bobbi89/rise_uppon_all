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

## Admin e gestione

Imposta `ADMIN_CHAT_ID` (anche multipli separati da virgola) per vedere ordini e pagamenti.

Comandi admin:
- `/admin` pannello comandi
- `/orders` ultimi ordini
- `/payments` ultimi pagamenti
- `/shipping_set <PAESE> <costo>` regole spedizione
- `/product_add <nome>|<prezzo>|<categoria>|<descrizione>` aggiungi prodotto custom
- `/skill_add <keyword>|<risposta>` aggiungi risposta rapida
- `/reload` ricarica catalogo
 - `/azienda_set <campo>|<valore>` aggiorna contatti azienda
 - `/pagamento_add <metodo>` aggiorna metodi pagamento

## B2B

Il bot riconosce "ristoratore" o "Partita IVA" e propone lo sconto professionale del 15%.
Puoi anche attivarlo con `/b2b`.

## Multi-lingua

Auto-detect IT/EN/DE e comando `/lingua it|en|de`.

## Tracking

Admin: `/tracking_add <order_id>|<carrier>|<code>|<status>|<url>`
Utente: `/tracking <order_id>`

## FAQ dinamiche

Admin: `/faq_add <keyword>|<risposta>` e `/faq_list`

## Promo stagionali

Admin: `/promo_set <stagione>|<testo>`

## Checkout

Se configuri `STRIPE_SECRET_KEY`, puoi generare link pagamento con `/checkout <importo>`.
Per crypto, usa `/crypto_set <network>|<address>` e il bot invia istruzioni.

## CRM leggero

Il bot salva preferenze (Moraiolo/Frantoio) e storico ordini in `data/customers.json`.
