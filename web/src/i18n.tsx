import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { CategoryFilter, Lang, Product } from "./types";
import { telegramLanguageCode } from "./telegram";

export const LANGS: { code: Lang; label: string; flag: string }[] = [
  { code: "it", label: "Italiano", flag: "🇮🇹" },
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "ro", label: "Română", flag: "🇷🇴" },
  { code: "es", label: "Español", flag: "🇪🇸" },
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
  tagline: { it: "Bio Marketplace", en: "Bio Marketplace", ro: "Bio Marketplace", es: "Bio Marketplace" },
  search: {
    it: "Cerca olio, vino, cosmetica…",
    en: "Search oil, wine, cosmetics…",
    ro: "Caută ulei, vin, cosmetice…",
    es: "Buscar aceite, vino, cosmética…",
  },
  close: { it: "Chiudi", en: "Close", ro: "Închide", es: "Cerrar" },
  adminPanel: { it: "Pannello admin", en: "Admin panel", ro: "Panou admin", es: "Panel admin" },
  myOrdersAria: { it: "I miei ordini", en: "My orders", ro: "Comenzile mele", es: "Mis pedidos" },
  openCart: { it: "Apri carrello", en: "Open cart", ro: "Deschide coșul", es: "Abrir carrito" },
  changeLang: { it: "Cambia lingua", en: "Change language", ro: "Schimbă limba", es: "Cambiar idioma" },

  // Griglia / App
  products: { it: "prodotti", en: "products", ro: "produse", es: "productos" },
  freeShipFrom: {
    it: "Spedizione gratis da {min}",
    en: "Free shipping from {min}",
    ro: "Livrare gratuită de la {min}",
    es: "Envío gratis desde {min}",
  },
  noResults: {
    it: "Nessun prodotto trovato. Prova un'altra ricerca.",
    en: "No products found. Try another search.",
    ro: "Niciun produs găsit. Încearcă altă căutare.",
    es: "No se encontraron productos. Prueba otra búsqueda.",
  },
  footerLine: {
    it: "Prodotti biologici italiani",
    en: "Italian organic products",
    ro: "Produse bio italiene",
    es: "Productos orgánicos italianos",
  },
  cartWord: { it: "Carrello", en: "Cart", ro: "Coș", es: "Carrito" },
  itemOne: { it: "articolo", en: "item", ro: "articol", es: "artículo" },
  itemMany: { it: "articoli", en: "items", ro: "articole", es: "artículos" },

  // Prodotto
  soldOut: { it: "Esaurito", en: "Sold out", ro: "Epuizat", es: "Agotado" },
  productDetail: { it: "Dettaglio prodotto", en: "Product detail", ro: "Detalii produs", es: "Detalle del producto" },
  add: { it: "Aggiungi", en: "Add", ro: "Adaugă", es: "Añadir" },

  // Carrello
  cartTitle: { it: "Il tuo carrello", en: "Your cart", ro: "Coșul tău", es: "Tu carrito" },
  cartEmpty: {
    it: "Il carrello è vuoto. Scopri i nostri prodotti biologici!",
    en: "Your cart is empty. Discover our organic products!",
    ro: "Coșul este gol. Descoperă produsele noastre bio!",
    es: "El carrito está vacío. ¡Descubre nuestros productos orgánicos!",
  },
  addForFree: {
    it: "Aggiungi {amount} per la spedizione gratuita 🚚",
    en: "Add {amount} for free shipping 🚚",
    ro: "Adaugă {amount} pentru livrare gratuită 🚚",
    es: "Añade {amount} para el envío gratis 🚚",
  },
  freeUnlocked: {
    it: "🎉 Spedizione gratuita sbloccata!",
    en: "🎉 Free shipping unlocked!",
    ro: "🎉 Livrare gratuită deblocată!",
    es: "🎉 ¡Envío gratis desbloqueado!",
  },
  subtotal: { it: "Subtotale", en: "Subtotal", ro: "Subtotal", es: "Subtotal" },
  shipping: { it: "Spedizione", en: "Shipping", ro: "Livrare", es: "Envío" },
  total: { it: "Totale", en: "Total", ro: "Total", es: "Total" },
  free: { it: "Gratis", en: "Free", ro: "Gratuit", es: "Gratis" },
  proceedCheckout: { it: "Procedi al checkout", en: "Proceed to checkout", ro: "Continuă la plată", es: "Ir a pagar" },

  // Checkout
  checkout: { it: "Checkout", en: "Checkout", ro: "Finalizare", es: "Pago" },
  summary: { it: "Riepilogo", en: "Summary", ro: "Rezumat", es: "Resumen" },
  fullName: { it: "Nome e cognome", en: "Full name", ro: "Nume și prenume", es: "Nombre y apellidos" },
  phone: { it: "Telefono", en: "Phone", ro: "Telefon", es: "Teléfono" },
  addressLine: { it: "Indirizzo e numero civico", en: "Address and number", ro: "Adresă și număr", es: "Dirección y número" },
  city: { it: "Città", en: "City", ro: "Oraș", es: "Ciudad" },
  zip: { it: "CAP", en: "ZIP", ro: "Cod poștal", es: "C.P." },
  country: { it: "Paese", en: "Country", ro: "Țară", es: "País" },
  notes: {
    it: "Note per il corriere (opzionale)",
    en: "Notes for courier (optional)",
    ro: "Note pentru curier (opțional)",
    es: "Notas para el mensajero (opcional)",
  },
  paymentMethod: { it: "Metodo di pagamento", en: "Payment method", ro: "Metodă de plată", es: "Método de pago" },
  cardRevolut: { it: "Carta / Revolut Pay", en: "Card / Revolut Pay", ro: "Card / Revolut Pay", es: "Tarjeta / Revolut Pay" },
  secureRevolut: {
    it: "Pagamento sicuro con Revolut (carta o Revolut Pay).",
    en: "Secure payment with Revolut (card or Revolut Pay).",
    ro: "Plată securizată cu Revolut (card sau Revolut Pay).",
    es: "Pago seguro con Revolut (tarjeta o Revolut Pay).",
  },
  paypalInfo: {
    it: "Con PayPal riceverai le istruzioni per pagare; l'ordine viene confermato alla ricezione.",
    en: "With PayPal you'll get payment instructions; the order is confirmed on receipt.",
    ro: "Cu PayPal vei primi instrucțiunile de plată; comanda se confirmă la primire.",
    es: "Con PayPal recibirás las instrucciones de pago; el pedido se confirma al recibirlo.",
  },
  noPayment: {
    it: "Pagamenti non ancora configurati: l'ordine verrà registrato e ti contatteremo.",
    en: "Payments not configured yet: the order will be registered and we'll contact you.",
    ro: "Plățile nu sunt încă configurate: comanda va fi înregistrată și te vom contacta.",
    es: "Pagos aún no configurados: el pedido se registrará y te contactaremos.",
  },
  pay: { it: "Paga", en: "Pay", ro: "Plătește", es: "Pagar" },
  payPaypal: {
    it: "Ordina e paga con PayPal",
    en: "Order and pay with PayPal",
    ro: "Comandă și plătește cu PayPal",
    es: "Pedir y pagar con PayPal",
  },
  processing: { it: "Elaborazione…", en: "Processing…", ro: "Se procesează…", es: "Procesando…" },
  paymentNotConfirmed: {
    it: "Pagamento non confermato. Riprova o contattaci.",
    en: "Payment not confirmed. Try again or contact us.",
    ro: "Plată neconfirmată. Încearcă din nou sau contactează-ne.",
    es: "Pago no confirmado. Inténtalo de nuevo o contáctanos.",
  },
  paymentError: {
    it: "Errore durante il pagamento.",
    en: "Error during payment.",
    ro: "Eroare în timpul plății.",
    es: "Error durante el pago.",
  },

  // Success
  orderConfirmed: { it: "Ordine confermato", en: "Order confirmed", ro: "Comandă confirmată", es: "Pedido confirmado" },
  orderRegistered: { it: "Ordine registrato", en: "Order registered", ro: "Comandă înregistrată", es: "Pedido registrado" },
  thanks: { it: "Grazie!", en: "Thank you!", ro: "Mulțumim!", es: "¡Gracias!" },
  successPaid: {
    it: "è stato pagato con successo. Lo trovi in “I miei ordini” con stato e tracking.",
    en: "was paid successfully. You'll find it in “My orders” with status and tracking.",
    ro: "a fost plătită cu succes. O găsești în „Comenzile mele” cu status și tracking.",
    es: "se pagó con éxito. Lo encontrarás en «Mis pedidos» con estado y seguimiento.",
  },
  successPaypal: {
    it: "è stato registrato. Completa il pagamento su PayPal per confermarlo.",
    en: "was registered. Complete the PayPal payment to confirm it.",
    ro: "a fost înregistrată. Finalizează plata PayPal pentru a o confirma.",
    es: "se registró. Completa el pago en PayPal para confirmarlo.",
  },
  successPending: {
    it: "è stato registrato. Ti contatteremo per completare il pagamento.",
    en: "was registered. We'll contact you to complete the payment.",
    ro: "a fost înregistrată. Te vom contacta pentru a finaliza plata.",
    es: "se registró. Te contactaremos para completar el pago.",
  },
  yourOrder: { it: "Il tuo ordine", en: "Your order", ro: "Comanda ta", es: "Tu pedido" },
  ofAmount: { it: "da", en: "of", ro: "de", es: "de" },
  paypalPayment: { it: "Pagamento PayPal", en: "PayPal payment", ro: "Plată PayPal", es: "Pago PayPal" },
  paypalSendTo: {
    it: "Invia {amount} a questo account PayPal:",
    en: "Send {amount} to this PayPal account:",
    ro: "Trimite {amount} către acest cont PayPal:",
    es: "Envía {amount} a esta cuenta PayPal:",
  },
  payWithPaypalMe: { it: "Paga con PayPal.me", en: "Pay with PayPal.me", ro: "Plătește cu PayPal.me", es: "Pagar con PayPal.me" },
  paypalReference: {
    it: "Indica il numero d'ordine {id} nella causale. Confermeremo la spedizione appena ricevuto il pagamento.",
    en: "Include the order number {id} in the note. We'll confirm shipping as soon as we receive payment.",
    ro: "Menționează numărul comenzii {id} la detalii. Vom confirma livrarea imediat ce primim plata.",
    es: "Indica el número de pedido {id} en el concepto. Confirmaremos el envío en cuanto recibamos el pago.",
  },
  continueShopping: { it: "Continua lo shopping", en: "Continue shopping", ro: "Continuă cumpărăturile", es: "Seguir comprando" },

  // Profilo
  loading: { it: "Caricamento…", en: "Loading…", ro: "Se încarcă…", es: "Cargando…" },
  loadError: { it: "Errore nel caricamento", en: "Loading error", ro: "Eroare la încărcare", es: "Error al cargar" },
  noOrders: { it: "Non hai ancora ordini.", en: "You have no orders yet.", ro: "Nu ai încă comenzi.", es: "Aún no tienes pedidos." },
  clearUnpaid: {
    it: "Svuota ordini non pagati ({n})",
    en: "Clear unpaid orders ({n})",
    ro: "Golește comenzile neplătite ({n})",
    es: "Vaciar pedidos no pagados ({n})",
  },
  shippedWith: { it: "Spedito con {carrier}", en: "Shipped with {carrier}", ro: "Expediat cu {carrier}", es: "Enviado con {carrier}" },
  trackCode: { it: "Codice", en: "Code", ro: "Cod", es: "Código" },
  trackShipment: {
    it: "Traccia la spedizione →",
    en: "Track shipment →",
    ro: "Urmărește livrarea →",
    es: "Rastrear envío →",
  },
  preparingNote: {
    it: "In preparazione — riceverai il codice di tracking qui.",
    en: "Preparing — you'll get the tracking code here.",
    ro: "În pregătire — vei primi codul de tracking aici.",
    es: "En preparación — recibirás el código de seguimiento aquí.",
  },

  // Stati ordine
  st_pending: { it: "Da pagare", en: "To pay", ro: "De plătit", es: "Por pagar" },
  st_awaiting_payment: { it: "PayPal in attesa", en: "PayPal pending", ro: "PayPal în așteptare", es: "PayPal pendiente" },
  st_paid: { it: "Pagato", en: "Paid", ro: "Plătit", es: "Pagado" },
  st_preparing: { it: "In preparazione", en: "Preparing", ro: "În pregătire", es: "En preparación" },
  st_shipped: { it: "Spedito", en: "Shipped", ro: "Expediat", es: "Enviado" },
  st_delivered: { it: "Consegnato", en: "Delivered", ro: "Livrat", es: "Entregado" },
  st_cancelled: { it: "Annullato", en: "Cancelled", ro: "Anulat", es: "Cancelado" },

  // Language gate
  chooseLanguage: { it: "Scegli la lingua", en: "Choose your language", ro: "Alege limba", es: "Elige el idioma" },
  gateSubtitle: {
    it: "Benvenuto in Oro Naturale · seleziona la lingua per continuare",
    en: "Welcome to Oro Naturale · select your language to continue",
    ro: "Bine ai venit la Oro Naturale · alege limba pentru a continua",
    es: "Bienvenido a Oro Naturale · selecciona el idioma para continuar",
  },
  continueBtn: { it: "Continua", en: "Continue", ro: "Continuă", es: "Continuar" },
};

const CATEGORY_LABELS: Record<CategoryFilter, Record<Lang, string>> = {
  all: { it: "Tutti", en: "All", ro: "Toate", es: "Todos" },
  extra_virgin_olive_oil: { it: "Extravergine", en: "Extra Virgin", ro: "Extravirgin", es: "Virgen Extra" },
  flavored_oils: { it: "Aromatizzati", en: "Flavored", ro: "Aromatizate", es: "Aromatizados" },
  wines: { it: "Vini", en: "Wines", ro: "Vinuri", es: "Vinos" },
  cosmetics: { it: "Cosmetica", en: "Cosmetics", ro: "Cosmetice", es: "Cosmética" },
  gift_boxes: { it: "Gift Box", en: "Gift Boxes", ro: "Gift Box", es: "Gift Box" },
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
