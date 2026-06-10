import { ArrowRight, BadgePercent, CreditCard, Truck } from "lucide-react";

type Props = {
  onCatalog: () => void;
  onCart: () => void;
};

export function Hero({ onCatalog, onCart }: Props) {
  return (
    <section className="relative overflow-hidden bg-olive-900 text-cream">
      <div
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=1800&q=80')",
          backgroundPosition: "center",
          backgroundSize: "cover",
        }}
      />
      <div className="relative mx-auto grid min-h-[560px] max-w-7xl content-end px-4 pb-10 pt-20 md:min-h-[620px]">
        <div className="max-w-3xl">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.25em] text-gold">EVO umbro, vini e gift box</p>
          <h1 className="font-display text-5xl leading-tight md:text-7xl">Oro Naturale</h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-cream/85">
            Shop Telegram premium per acquistare oli, vini e prodotti gourmet con carrello, checkout Stripe o Revolut Pay,
            ordini e tracking in un unico flusso.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button className="inline-flex items-center gap-2 rounded bg-gold px-5 py-3 font-bold text-olive-900" onClick={onCatalog}>
              Sfoglia catalogo
              <ArrowRight size={18} />
            </button>
            <button className="inline-flex items-center gap-2 rounded border border-cream/40 px-5 py-3 font-bold text-cream" onClick={onCart}>
              Vai al carrello
            </button>
          </div>
        </div>
        <div className="mt-10 grid gap-3 sm:grid-cols-3">
          <div className="flex items-center gap-3 border-t border-cream/25 pt-4">
            <CreditCard size={20} className="text-gold" />
            <span className="text-sm text-cream/85">Stripe e Revolut Pay</span>
          </div>
          <div className="flex items-center gap-3 border-t border-cream/25 pt-4">
            <Truck size={20} className="text-gold" />
            <span className="text-sm text-cream/85">Tracking ordine integrato</span>
          </div>
          <div className="flex items-center gap-3 border-t border-cream/25 pt-4">
            <BadgePercent size={20} className="text-gold" />
            <span className="text-sm text-cream/85">B2B e sconti gestibili</span>
          </div>
        </div>
      </div>
    </section>
  );
}
