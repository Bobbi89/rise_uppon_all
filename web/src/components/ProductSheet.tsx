import { useEffect, useState } from "react";
import { Minus, Plus, ShoppingBag } from "lucide-react";
import type { Product } from "../types";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

type Props = {
  product: Product | null;
  onClose: () => void;
  onAdd: (product: Product, quantity: number) => void;
};

export function ProductSheet({ product, onClose, onAdd }: Props) {
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    setQuantity(1);
  }, [product?.id]);

  return (
    <Sheet open={product !== null} title="Dettaglio prodotto" onClose={onClose}>
      {product && (
        <div className="px-5 pb-5">
          <div className="overflow-hidden rounded-2xl bg-olive-50">
            <img src={product.image} alt={product.name} className="aspect-square w-full object-cover" />
          </div>

          <div className="mt-4 flex items-start justify-between gap-3">
            <h3 className="font-display text-xl font-semibold leading-snug text-olive-900">
              {product.name}
            </h3>
            <span className="shrink-0 text-xl font-extrabold text-olive-900">
              {formatMoney(product.price)}
            </span>
          </div>

          {(product.volume || product.origin) && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {product.volume && (
                <span className="rounded-full bg-olive-100 px-2.5 py-1 text-[11px] font-bold text-olive-700">
                  {product.volume}
                </span>
              )}
              {product.origin && (
                <span className="rounded-full bg-olive-100 px-2.5 py-1 text-[11px] font-bold text-olive-700">
                  📍 {product.origin}
                </span>
              )}
            </div>
          )}

          <p className="mt-3 text-sm leading-6 text-olive-700">{product.description}</p>

          {product.tags && product.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {product.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-gold/40 bg-gold/10 px-2.5 py-1 text-[11px] font-bold text-clay"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          <div className="safe-bottom mt-5 flex items-center gap-3">
            <div className="flex items-center gap-1 rounded-full border border-olive-100 bg-white p-1">
              <button
                aria-label="Diminuisci quantità"
                className="grid h-9 w-9 place-items-center rounded-full text-olive-700"
                onClick={() => setQuantity((value) => Math.max(1, value - 1))}
              >
                <Minus size={16} />
              </button>
              <span className="w-7 text-center text-sm font-extrabold text-olive-900">{quantity}</span>
              <button
                aria-label="Aumenta quantità"
                className="grid h-9 w-9 place-items-center rounded-full text-olive-700"
                onClick={() => setQuantity((value) => value + 1)}
              >
                <Plus size={16} />
              </button>
            </div>
            <button
              disabled={product.stock <= 0}
              className="flex flex-1 items-center justify-center gap-2 rounded-full bg-olive-900 py-3.5 text-sm font-extrabold text-cream active:scale-[0.98]"
              onClick={() => onAdd(product, quantity)}
            >
              <ShoppingBag size={16} />
              Aggiungi · {formatMoney(product.price * quantity)}
            </button>
          </div>
        </div>
      )}
    </Sheet>
  );
}
