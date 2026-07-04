# Oro Naturale Telegram Agent

Telegram bot per promuovere i prodotti Oro Naturale e rispondere a richieste di catalogo, prezzi e ordini.

## Mini App (marketplace in-chat)

Nella cartella `web/` c'è la Mini App Telegram: un marketplace biologico mobile-first
con griglia prodotti compatta a 2/3 colonne, ricerca, filtri per categoria,
scheda prodotto, carrello e checkout in bottom sheet — tutto in stile app Telegram.

```bash
cd web
npm install
npm run dev      # sviluppo su http://localhost:5173
npm run build    # build di produzione in web/dist
```

### Deploy su Railway (servizio unico — consigliato)

Lo **stesso processo** che esegue il bot serve anche la Mini App. All'avvio,
se Railway fornisce una `PORT`, `main.py` apre un web server (aiohttp) che
distribuisce `web/dist` e Railway gli assegna un dominio HTTPS pubblico.

Non serve configurare nulla a mano:

1. Railway inietta automaticamente `PORT` e `RAILWAY_PUBLIC_DOMAIN`.
2. `WEBAPP_URL` viene ricavata dal dominio Railway se non impostata
   esplicitamente, quindi la Mini App è raggiungibile senza variabili extra.
3. All'avvio il bot imposta da solo, via Bot API:
   - il **pulsante-menu Mini App** (accanto alla casella di testo) → apre il negozio;
   - il **menu comandi** `/start`, `/catalogo`, `/carrello`, …
4. Il pulsante **🌿 Apri il Negozio** appare anche nel menu principale e nel
   benvenuto. Gli ordini confermati arrivano al bot via `web_app_data`:
   l'utente riceve la conferma in chat e gli admin la notifica.

> `web/dist` è committato nel repo: Railway serve subito la Mini App eseguendo
> solo `python main.py`. Dopo modifiche a `web/src`, rilancia
> `npm --prefix web run build` e ricommitta `web/dist`.

Per usare un hosting esterno (Vercel, Netlify, GitHub Pages) invece del
servizio unico, basta impostare `WEBAPP_URL=https://tuo-dominio` su Railway:
ha priorità sul dominio automatico.

### Deploy alternativo (GitHub Pages)

Il workflow `.github/workflows/deploy-miniapp.yml` compila la Mini App e la
pubblica sul branch `gh-pages` a ogni push che tocca `web/` o `deploy/`.
Attivalo una tantum in *Settings → Pages → Source: branch `gh-pages` / root*;
il sito sarà su `https://bobbi89.github.io/rise_uppon_all/`.

Il catalogo della Mini App è generato da `products.json`
(file `web/src/data/products.ts`).

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
python main.py
```

## Comandi

- `/catalogo` tutti i prodotti dal CSV
- `/olio` extravergini
- `/aromatizzati` oli aromatizzati
- `/vini` vini e spumanti
- `/cosmetici` cosmetici
- `/gift` confezioni regalo
- `/ordine` richiede i dati per ordine
- `/carrello` mostra il carrello
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

## Uso dal mobile

Se vuoi lavorare da telefono, la strada piu semplice e' usare **Termux** su Android oppure **GitHub Mobile + Railway web**.

### Pacchetti utili su Termux

Installa questi strumenti:
- `git`
- `python`
- `nodejs`
- `npm`

Poi installa la CLI di Railway:

```bash
npm install -g @railway/cli
```

### Setup rapido su Termux

```bash
pkg update
pkg install git python nodejs
pip install -r requirements.txt
npm install -g @railway/cli
```

### Flusso consigliato dal telefono

1. Fai le modifiche al codice.
2. Esegui `git add`, `git commit` e `git push`.
3. Apri Railway dal browser mobile e lascia fare il redeploy automatico.

Se preferisci, puoi anche evitare la CLI e usare solo:
- GitHub app per il push
- Railway dashboard mobile per il deploy

## Admin e gestione

Imposta `ADMIN_CHAT_ID` (anche multipli separati da virgola) per vedere ordini e pagamenti.

Comandi admin:
- `/admin` pannello comandi
- `/orders` ultimi ordini
- `/payments` ultimi pagamenti
- `/shipping_set <PAESE> <costo>` regole spedizione
- `/product_add <nome>|<prezzo>|<categoria>|<descrizione>|[image_url]` aggiungi prodotto custom (foto opzionale)
- `/skill_add <keyword>|<risposta>` aggiungi risposta rapida
- `/reload` ricarica catalogo
 - `/azienda_set <campo>|<valore>` aggiorna contatti azienda
 - `/pagamento_add <metodo>` aggiorna metodi pagamento

## Menu iniziale

Il menu pubblico offre scorciatoie per:
- Catalogo
- Carrello
- Fai un ordine
- Pagamenti
- Spedizione
- Contatti
- Area B2B
- Info & FAQ

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

## Sales flow

Il bot usa uno stage semplice (qualify, order_collect, payment_pending). Puoi resettare con `/reset`.
Include follow-up automatico dopo 24h se il pagamento non e' completato.

## Nuova architettura

La versione attiva ora è modulare:
- `main.py` entrypoint
- `oro_naturale/config.py` configurazione
- `oro_naturale/storage.py` persistenza file-based
- `oro_naturale/keyboards.py` pulsanti e menu
- `oro_naturale/services.py` ordini, Stripe, follow-up
- `oro_naturale/routers/public.py` flusso clienti
- `oro_naturale/routers/admin.py` pannello privato
