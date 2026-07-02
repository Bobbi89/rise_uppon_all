import { Plus } from "lucide-react";
import type { Product } from "../types";
import { formatMoney } from "../utils/money";

type Props = {
  product: Product;
  onAdd: (product: Product) => void;
  onView: (product: Product) => void;
};

/** Card compatta per la griglia 2/3 colonne, stile mini app Telegram. */
export function ProductCard({ product, onAdd, onView }: Props) {
  const soldOut = product.stock <= 0;
  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-olive-100/70 bg-white shadow-card">
      <button className="relative block w-full text-left" onClick={() => onView(product)}>
        <div className="aspect-square overflow-hidden bg-olive-50">
          <img
            src={product.image}
            alt={product.name}
            loading="lazy"
            className="h-full w-full object-cover"
          />
        </div>
        {product.volume && (
          <span className="absolute left-2 top-2 rounded-full bg-olive-900/75 px-2 py-0.5 text-[10px] font-bold text-cream backdrop-blur-sm">
            {product.volume}
          </span>
        )}
        {soldOut && (
          <span className="absolute inset-x-2 bottom-2 rounded-lg bg-clay/90 py-1 text-center text-[11px] font-bold text-cream">
            Esaurito
          </span>
        )}
      </button>
      <div className="flex flex-1 flex-col p-2.5">
        <button className="text-left" onClick={() => onView(product)}>
          <h3 className="line-clamp-2 min-h-[32px] text-[13px] font-bold leading-4 text-olive-900">
            {product.name}
          </h3>
        </button>
        <div className="mt-auto flex items-center justify-between pt-2">
          <span className="text-sm font-extrabold text-olive-900">{formatMoney(product.price)}</span>
          <button
            aria-label={`Aggiungi ${product.name} al carrello`}
            disabled={soldOut}
            onClick={() => onAdd(product)}
            className="grid h-8 w-8 place-items-center rounded-full bg-olive-900 text-cream active:scale-95"
          >
            <Plus size={16} strokeWidth={2.5} />
          </button>
        </div>
      </div>
    </article>
  );
}
