// Regole di spedizione allineate a biomarketshop.com:
//   • Ordine ≥ 69 € → spedizione gratuita
//   • Italia + Europa (GLS) → 10,40 €
//   • Paesi nordici → 14 €
//   • Resto del mondo (DHL) → 25 €

export const FREE_SHIPPING_MIN = 69;

const NORDIC = ["SE", "NO", "DK", "FI", "IS"];
const EUROPE = ["IT", "FR", "ES", "DE", "AT", "BE", "NL", "PT", "GR", "IE", "LU", "CH", "GB"];

export const EUROPE_SHIPPING = 10.4;
export const NORDIC_SHIPPING = 14;
export const WORLD_SHIPPING = 25;

/** Costo di spedizione per subtotale e paese (ISO-2). */
export function shippingFor(subtotal: number, country = "IT"): number {
  if (subtotal >= FREE_SHIPPING_MIN) return 0;
  const c = (country || "IT").toUpperCase();
  if (NORDIC.includes(c)) return NORDIC_SHIPPING;
  if (EUROPE.includes(c)) return EUROPE_SHIPPING;
  return WORLD_SHIPPING;
}

/** Paesi selezionabili al checkout (etichette in italiano/inglese neutro). */
export const COUNTRIES: { code: string; name: string }[] = [
  { code: "IT", name: "Italia / Italy" },
  { code: "FR", name: "France" },
  { code: "ES", name: "España" },
  { code: "DE", name: "Deutschland" },
  { code: "AT", name: "Österreich" },
  { code: "BE", name: "Belgique" },
  { code: "NL", name: "Nederland" },
  { code: "PT", name: "Portugal" },
  { code: "GR", name: "Ελλάδα" },
  { code: "IE", name: "Ireland" },
  { code: "LU", name: "Luxembourg" },
  { code: "CH", name: "Schweiz" },
  { code: "GB", name: "United Kingdom" },
  { code: "SE", name: "Sverige" },
  { code: "NO", name: "Norge" },
  { code: "DK", name: "Danmark" },
  { code: "FI", name: "Suomi" },
  { code: "IS", name: "Ísland" },
  { code: "RO", name: "România" },
  { code: "OTHER", name: "Other / Altro" },
];
