import { Info, Minus, Plus } from "lucide-react";
import { localizeProduct, useI18n } from "../i18n";
import type { Product } from "../types";
import { formatMoney } from "../utils/money";

type Props = {
  product: Product;
  quantity: number;
  onAdd: (product: Product) => void;
  onDecrement: (product: Product) => void;
  onView: (product: Product) => void;
};

/** Card compatta per la griglia 2/3 colonne, stile mini app Telegram. */
export function ProductCard({ product, quantity, onAdd, onDecrement, onView }: Props) {
  const { lang, t } = useI18n();
  const { name } = localizeProduct(product, lang);
  const soldOut = product.stock <= 0;
  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-olive-100/70 bg-white shadow-card">
      <div className="relative">
        <button
          className="block w-full text-left"
          onClick={() => onView(product)}
          aria-label={`Apri ${name}`}
        >
          <div className="aspect-square overflow-hidden bg-olive-50">
            <img
              src={product.image}
              alt={name}
              loading="lazy"
              className="h-full w-full object-cover"
            />
          </div>
        </button>

        {product.volume && (
          <span className="absolute left-2 top-2 rounded-full bg-olive-900/75 px-2 py-0.5 text-[10px] font-bold text-cream backdrop-blur-sm">
            {product.volume}
          </span>
        )}

        {/* Pulsante (i) — apre descrizione e dettagli */}
        <button
          aria-label={`Descrizione e dettagli di ${name}`}
          onClick={() => onView(product)}
          className="absolute right-2 top-2 grid h-7 w-7 place-items-center rounded-full bg-white/85 text-olive-900 shadow-sm backdrop-blur-sm active:scale-90"
        >
          <Info size={15} strokeWidth={2.5} />
        </button>

        {soldOut && (
          <span className="absolute inset-x-2 bottom-2 rounded-lg bg-clay/90 py-1 text-center text-[11px] font-bold text-cream">
            {t("soldOut")}
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col p-2.5">
        <button className="text-left" onClick={() => onView(product)}>
          <h3 className="line-clamp-2 min-h-[32px] text-[13px] font-bold leading-4 text-olive-900">
            {name}
          </h3>
        </button>

        <div className="mt-auto flex items-center justify-between gap-2 pt-2">
          <span className="text-sm font-extrabold text-olive-900">{formatMoney(product.price)}</span>

          {quantity === 0 ? (
            <button
              aria-label={`Aggiungi ${name} al carrello`}
              disabled={soldOut}
              onClick={() => onAdd(product)}
              className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-olive-900 text-cream active:scale-95"
            >
              <Plus size={16} strokeWidth={2.5} />
            </button>
          ) : (
            <div className="flex shrink-0 items-center rounded-full bg-olive-900 text-cream">
              <button
                aria-label={`Togli un ${name}`}
                onClick={() => onDecrement(product)}
                className="grid h-8 w-8 place-items-center rounded-full active:scale-90"
              >
                <Minus size={15} strokeWidth={2.5} />
              </button>
              <span className="min-w-[18px] text-center text-sm font-extrabold tabular-nums">
                {quantity}
              </span>
              <button
                aria-label={`Aggiungi un altro ${name}`}
                disabled={soldOut}
                onClick={() => onAdd(product)}
                className="grid h-8 w-8 place-items-center rounded-full active:scale-90"
              >
                <Plus size={15} strokeWidth={2.5} />
              </button>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}
