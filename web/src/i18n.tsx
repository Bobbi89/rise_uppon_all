import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { CategoryFilter, Lang, Product } from "./types";
import { telegramLanguageCode } from "./telegram";

export const LANGS: { code: Lang; label: string; flag: string }[] = [
  { code: "it", label: "Italiano", flag: "🇮🇹" },
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "ro", label: "Română", flag: "🇷🇴" },
  { code: "es", label: "Español", flag: "🇪🇸" },
  { code: "no", label: "Norsk", flag: "🇳🇴" },
];

const STORAGE_KEY = "oro_lang";

export function storedLang(): Lang | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v && LANGS.some((l) => l.code === v) ? (v as Lang) : null;
  } catch {
    return null;
  }
}

/** Lingua di default: quella salvata, altrimenti quella di Telegram, altrimenti it. */
export function detectLang(): Lang {
  const saved = storedLang();
  if (saved) return saved;
  const tg = (telegramLanguageCode() || "").slice(0, 2).toLowerCase();
  const match = LANGS.find((l) => l.code === tg);
  return match ? match.code : "it";
}

type Dict = Record<string, Record<Lang, string>>;

// Stringhe UI. Ogni chiave ha le 4 lingue. {placeholder} viene interpolato da t().
const STRINGS: Dict = {
  tagline: { it: "Bio Marketplace", en: "Bio Marketplace", ro: "Bio Marketplace", es: "Bio Marketplace", no: "Bio Marketplace" },
  search: {
    it: "Cerca olio, vino, cosmetica…",
    en: "Search oil, wine, cosmetics…",
    ro: "Caută ulei, vin, cosmetice…",
    es: "Buscar aceite, vino, cosmética…", no: "Søk olje, vin, kosmetikk…",
  },
  close: { it: "Chiudi", en: "Close", ro: "Închide", es: "Cerrar", no: "Lukk" },
  adminPanel: { it: "Pannello admin", en: "Admin panel", ro: "Panou admin", es: "Panel admin", no: "Adminpanel" },
  myOrdersAria: { it: "I miei ordini", en: "My orders", ro: "Comenzile mele", es: "Mis pedidos", no: "Mine bestillinger" },
  openCart: { it: "Apri carrello", en: "Open cart", ro: "Deschide coșul", es: "Abrir carrito", no: "Åpne handlekurv" },
  changeLang: { it: "Cambia lingua", en: "Change language", ro: "Schimbă limba", es: "Cambiar idioma", no: "Endre språk" },

  // Griglia / App
  products: { it: "prodotti", en: "products", ro: "produse", es: "productos", no: "produkter" },
  freeShipFrom: {
    it: "Spedizione gratis da {min}",
    en: "Free shipping from {min}",
    ro: "Livrare gratuită de la {min}",
    es: "Envío gratis desde {min}", no: "Gratis frakt fra {min}",
  },
  noResults: {
    it: "Nessun prodotto trovato. Prova un'altra ricerca.",
    en: "No products found. Try another search.",
    ro: "Niciun produs găsit. Încearcă altă căutare.",
    es: "No se encontraron productos. Prueba otra búsqueda.", no: "Ingen produkter funnet. Prøv et annet søk.",
  },
  footerLine: {
    it: "Prodotti biologici italiani",
    en: "Italian organic products",
    ro: "Produse bio italiene",
    es: "Productos orgánicos italianos", no: "Italienske økologiske produkter",
  },
  cartWord: { it: "Carrello", en: "Cart", ro: "Coș", es: "Carrito", no: "Handlekurv" },
  itemOne: { it: "articolo", en: "item", ro: "articol", es: "artículo", no: "vare" },
  itemMany: { it: "articoli", en: "items", ro: "articole", es: "artículos", no: "varer" },

  // Prodotto
  soldOut: { it: "Esaurito", en: "Sold out", ro: "Epuizat", es: "Agotado", no: "Utsolgt" },
  productDetail: { it: "Dettaglio prodotto", en: "Product detail", ro: "Detalii produs", es: "Detalle del producto", no: "Produktdetaljer" },
  add: { it: "Aggiungi", en: "Add", ro: "Adaugă", es: "Añadir", no: "Legg til" },

  // Carrello
  cartTitle: { it: "Il tuo carrello", en: "Your cart", ro: "Coșul tău", es: "Tu carrito", no: "Handlekurven din" },
  cartEmpty: {
    it: "Il carrello è vuoto. Scopri i nostri prodotti biologici!",
    en: "Your cart is empty. Discover our organic products!",
    ro: "Coșul este gol. Descoperă produsele noastre bio!",
    es: "El carrito está vacío. ¡Descubre nuestros productos orgánicos!", no: "Handlekurven er tom. Oppdag våre økologiske produkter!",
  },
  addForFree: {
    it: "Aggiungi {amount} per la spedizione gratuita 🚚",
    en: "Add {amount} for free shipping 🚚",
    ro: "Adaugă {amount} pentru livrare gratuită 🚚",
    es: "Añade {amount} para el envío gratis 🚚", no: "Legg til {amount} for gratis frakt 🚚",
  },
  freeUnlocked: {
    it: "🎉 Spedizione gratuita sbloccata!",
    en: "🎉 Free shipping unlocked!",
    ro: "🎉 Livrare gratuită deblocată!",
    es: "🎉 ¡Envío gratis desbloqueado!", no: "🎉 Gratis frakt låst opp!",
  },
  subtotal: { it: "Subtotale", en: "Subtotal", ro: "Subtotal", es: "Subtotal", no: "Delsum" },
  shipping: { it: "Spedizione", en: "Shipping", ro: "Livrare", es: "Envío", no: "Frakt" },
  total: { it: "Totale", en: "Total", ro: "Total", es: "Total", no: "Totalt" },
  free: { it: "Gratis", en: "Free", ro: "Gratuit", es: "Gratis", no: "Gratis" },
  proceedCheckout: { it: "Procedi al checkout", en: "Proceed to checkout", ro: "Continuă la plată", es: "Ir a pagar", no: "Gå til kassen" },

  // Checkout
  checkout: { it: "Checkout", en: "Checkout", ro: "Finalizare", es: "Pago", no: "Kasse" },
  summary: { it: "Riepilogo", en: "Summary", ro: "Rezumat", es: "Resumen", no: "Oppsummering" },
  fullName: { it: "Nome e cognome", en: "Full name", ro: "Nume și prenume", es: "Nombre y apellidos", no: "Fullt navn" },
  phone: { it: "Telefono", en: "Phone", ro: "Telefon", es: "Teléfono", no: "Telefon" },
  addressLine: { it: "Indirizzo e numero civico", en: "Address and number", ro: "Adresă și număr", es: "Dirección y número", no: "Adresse og husnummer" },
  city: { it: "Città", en: "City", ro: "Oraș", es: "Ciudad", no: "By" },
  zip: { it: "CAP", en: "ZIP", ro: "Cod poștal", es: "C.P.", no: "Postnummer" },
  country: { it: "Paese", en: "Country", ro: "Țară", es: "País", no: "Land" },
  notes: {
    it: "Note per il corriere (opzionale)",
    en: "Notes for courier (optional)",
    ro: "Note pentru curier (opțional)",
    es: "Notas para el mensajero (opcional)", no: "Melding til budet (valgfritt)",
  },
  paymentMethod: { it: "Metodo di pagamento", en: "Payment method", ro: "Metodă de plată", es: "Método de pago", no: "Betalingsmåte" },
  cardRevolut: { it: "Carta / Revolut Pay", en: "Card / Revolut Pay", ro: "Card / Revolut Pay", es: "Tarjeta / Revolut Pay", no: "Kort / Revolut Pay" },
  secureRevolut: {
    it: "Pagamento sicuro con Revolut (carta o Revolut Pay).",
    en: "Secure payment with Revolut (card or Revolut Pay).",
    ro: "Plată securizată cu Revolut (card sau Revolut Pay).",
    es: "Pago seguro con Revolut (tarjeta o Revolut Pay).", no: "Sikker betaling med Revolut (kort eller Revolut Pay).",
  },
  paypalInfo: {
    it: "Con PayPal riceverai le istruzioni per pagare; l'ordine viene confermato alla ricezione.",
    en: "With PayPal you'll get payment instructions; the order is confirmed on receipt.",
    ro: "Cu PayPal vei primi instrucțiunile de plată; comanda se confirmă la primire.",
    es: "Con PayPal recibirás las instrucciones de pago; el pedido se confirma al recibirlo.", no: "Med PayPal får du betalingsinstruksjoner; bestillingen bekreftes ved mottak.",
  },
  noPayment: {
    it: "Pagamenti non ancora configurati: l'ordine verrà registrato e ti contatteremo.",
    en: "Payments not configured yet: the order will be registered and we'll contact you.",
    ro: "Plățile nu sunt încă configurate: comanda va fi înregistrată și te vom contacta.",
    es: "Pagos aún no configurados: el pedido se registrará y te contactaremos.", no: "Betaling er ikke konfigurert ennå: bestillingen registreres og vi kontakter deg.",
  },
  pay: { it: "Paga", en: "Pay", ro: "Plătește", es: "Pagar", no: "Betal" },
  payPaypal: {
    it: "Ordina e paga con PayPal",
    en: "Order and pay with PayPal",
    ro: "Comandă și plătește cu PayPal",
    es: "Pedir y pagar con PayPal", no: "Bestill og betal med PayPal",
  },
  processing: { it: "Elaborazione…", en: "Processing…", ro: "Se procesează…", es: "Procesando…", no: "Behandler…" },
  paymentNotConfirmed: {
    it: "Pagamento non confermato. Riprova o contattaci.",
    en: "Payment not confirmed. Try again or contact us.",
    ro: "Plată neconfirmată. Încearcă din nou sau contactează-ne.",
    es: "Pago no confirmado. Inténtalo de nuevo o contáctanos.", no: "Betaling ikke bekreftet. Prøv igjen eller kontakt oss.",
  },
  paymentError: {
    it: "Errore durante il pagamento.",
    en: "Error during payment.",
    ro: "Eroare în timpul plății.",
    es: "Error durante el pago.", no: "Feil under betaling.",
  },

  // Success
  orderConfirmed: { it: "Ordine confermato", en: "Order confirmed", ro: "Comandă confirmată", es: "Pedido confirmado", no: "Bestilling bekreftet" },
  orderRegistered: { it: "Ordine registrato", en: "Order registered", ro: "Comandă înregistrată", es: "Pedido registrado", no: "Bestilling registrert" },
  thanks: { it: "Grazie!", en: "Thank you!", ro: "Mulțumim!", es: "¡Gracias!", no: "Takk!" },
  successPaid: {
    it: "è stato pagato con successo. Lo trovi in “I miei ordini” con stato e tracking.",
    en: "was paid successfully. You'll find it in “My orders” with status and tracking.",
    ro: "a fost plătită cu succes. O găsești în „Comenzile mele” cu status și tracking.",
    es: "se pagó con éxito. Lo encontrarás en «Mis pedidos» con estado y seguimiento.", no: "ble betalt. Du finner den i «Mine bestillinger» med status og sporing.",
  },
  successPaypal: {
    it: "è stato registrato. Completa il pagamento su PayPal per confermarlo.",
    en: "was registered. Complete the PayPal payment to confirm it.",
    ro: "a fost înregistrată. Finalizează plata PayPal pentru a o confirma.",
    es: "se registró. Completa el pago en PayPal para confirmarlo.", no: "ble registrert. Fullfør PayPal-betalingen for å bekrefte den.",
  },
  successPending: {
    it: "è stato registrato. Ti contatteremo per completare il pagamento.",
    en: "was registered. We'll contact you to complete the payment.",
    ro: "a fost înregistrată. Te vom contacta pentru a finaliza plata.",
    es: "se registró. Te contactaremos para completar el pago.", no: "ble registrert. Vi kontakter deg for å fullføre betalingen.",
  },
  yourOrder: { it: "Il tuo ordine", en: "Your order", ro: "Comanda ta", es: "Tu pedido", no: "Bestillingen din" },
  ofAmount: { it: "da", en: "of", ro: "de", es: "de", no: "på" },
  paypalPayment: { it: "Pagamento PayPal", en: "PayPal payment", ro: "Plată PayPal", es: "Pago PayPal", no: "PayPal-betaling" },
  paypalSendTo: {
    it: "Invia {amount} a questo account PayPal:",
    en: "Send {amount} to this PayPal account:",
    ro: "Trimite {amount} către acest cont PayPal:",
    es: "Envía {amount} a esta cuenta PayPal:", no: "Send {amount} til denne PayPal-kontoen:",
  },
  payWithPaypalMe: { it: "Paga con PayPal.me", en: "Pay with PayPal.me", ro: "Plătește cu PayPal.me", es: "Pagar con PayPal.me", no: "Betal med PayPal.me" },
  paypalReference: {
    it: "Indica il numero d'ordine {id} nella causale. Confermeremo la spedizione appena ricevuto il pagamento.",
    en: "Include the order number {id} in the note. We'll confirm shipping as soon as we receive payment.",
    ro: "Menționează numărul comenzii {id} la detalii. Vom confirma livrarea imediat ce primim plata.",
    es: "Indica el número de pedido {id} en el concepto. Confirmaremos el envío en cuanto recibamos el pago.", no: "Oppgi bestillingsnummeret {id} i meldingen. Vi bekrefter forsendelsen så snart betalingen er mottatt.",
  },
  continueShopping: { it: "Continua lo shopping", en: "Continue shopping", ro: "Continuă cumpărăturile", es: "Seguir comprando", no: "Fortsett å handle" },

  // Profilo
  loading: { it: "Caricamento…", en: "Loading…", ro: "Se încarcă…", es: "Cargando…", no: "Laster…" },
  loadError: { it: "Errore nel caricamento", en: "Loading error", ro: "Eroare la încărcare", es: "Error al cargar", no: "Feil ved innlasting" },
  noOrders: { it: "Non hai ancora ordini.", en: "You have no orders yet.", ro: "Nu ai încă comenzi.", es: "Aún no tienes pedidos.", no: "Du har ingen bestillinger ennå." },
  clearUnpaid: {
    it: "Svuota ordini non pagati ({n})",
    en: "Clear unpaid orders ({n})",
    ro: "Golește comenzile neplătite ({n})",
    es: "Vaciar pedidos no pagados ({n})", no: "Tøm ubetalte bestillinger ({n})",
  },
  shippedWith: { it: "Spedito con {carrier}", en: "Shipped with {carrier}", ro: "Expediat cu {carrier}", es: "Enviado con {carrier}", no: "Sendt med {carrier}" },
  trackCode: { it: "Codice", en: "Code", ro: "Cod", es: "Código", no: "Kode" },
  trackShipment: {
    it: "Traccia la spedizione →",
    en: "Track shipment →",
    ro: "Urmărește livrarea →",
    es: "Rastrear envío →", no: "Spor forsendelsen →",
  },
  preparingNote: {
    it: "In preparazione — riceverai il codice di tracking qui.",
    en: "Preparing — you'll get the tracking code here.",
    ro: "În pregătire — vei primi codul de tracking aici.",
    es: "En preparación — recibirás el código de seguimiento aquí.", no: "Under klargjøring — du får sporingskoden her.",
  },

  // Stati ordine
  st_pending: { it: "Da pagare", en: "To pay", ro: "De plătit", es: "Por pagar", no: "Må betales" },
  st_awaiting_payment: { it: "PayPal in attesa", en: "PayPal pending", ro: "PayPal în așteptare", es: "PayPal pendiente", no: "PayPal venter" },
  st_paid: { it: "Pagato", en: "Paid", ro: "Plătit", es: "Pagado", no: "Betalt" },
  st_preparing: { it: "In preparazione", en: "Preparing", ro: "În pregătire", es: "En preparación", no: "Under klargjøring" },
  st_shipped: { it: "Spedito", en: "Shipped", ro: "Expediat", es: "Enviado", no: "Sendt" },
  st_delivered: { it: "Consegnato", en: "Delivered", ro: "Livrat", es: "Entregado", no: "Levert" },
  st_cancelled: { it: "Annullato", en: "Cancelled", ro: "Anulat", es: "Cancelado", no: "Kansellert" },

  // Language gate
  chooseLanguage: { it: "Scegli la lingua", en: "Choose your language", ro: "Alege limba", es: "Elige el idioma", no: "Velg språk" },
  gateSubtitle: {
    it: "Benvenuto in Oro Naturale · seleziona la lingua per continuare",
    en: "Welcome to Oro Naturale · select your language to continue",
    ro: "Bine ai venit la Oro Naturale · alege limba pentru a continua",
    es: "Bienvenido a Oro Naturale · selecciona el idioma para continuar", no: "Velkommen til Oro Naturale · velg språk for å fortsette",
  },
  continueBtn: { it: "Continua", en: "Continue", ro: "Continuă", es: "Continuar", no: "Fortsett" },
};

const CATEGORY_LABELS: Record<CategoryFilter, Record<Lang, string>> = {
  all: { it: "Tutti", en: "All", ro: "Toate", es: "Todos", no: "Alle" },
  extra_virgin_olive_oil: { it: "Extravergine", en: "Extra Virgin", ro: "Extravirgin", es: "Virgen Extra", no: "Ekstra virgin" },
  flavored_oils: { it: "Aromatizzati", en: "Flavored", ro: "Aromatizate", es: "Aromatizados", no: "Aromatiserte" },
  wines: { it: "Vini", en: "Wines", ro: "Vinuri", es: "Vinos", no: "Viner" },
  cosmetics: { it: "Cosmetica", en: "Cosmetics", ro: "Cosmetice", es: "Cosmética", no: "Kosmetikk" },
  gift_boxes: { it: "Gift Box", en: "Gift Boxes", ro: "Gift Box", es: "Gift Box", no: "Gaveesker" },
};

/** Nome + descrizione del prodotto nella lingua richiesta (fallback su italiano). */
export function localizeProduct(product: Product, lang: Lang): { name: string; description: string } {
  if (lang === "it") return { name: product.name, description: product.description };
  const t = product.translations?.[lang];
  return {
    name: t?.name || product.name,
    description: t?.description || product.description,
  };
}

export function localizeCategory(id: CategoryFilter, lang: Lang): string {
  return CATEGORY_LABELS[id]?.[lang] ?? id;
}

type I18nValue = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: keyof typeof STRINGS | string, params?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => detectLang());

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* storage non disponibile */
    }
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>) => {
      const entry = STRINGS[key];
      let s = entry ? entry[lang] : key;
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
        }
      }
      return s;
    },
    [lang],
  );

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
