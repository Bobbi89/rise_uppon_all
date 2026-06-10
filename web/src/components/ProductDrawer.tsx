import { Minus, Plus, X } from "lucide-react";
import { useState } from "react";
import type { Product } from "../types";
import { formatMoney } from "../utils/money";

type Props = {
  product: Product | null;
  related: Product[];
  onClose: () => void;
  onAdd: (product: Product, quantity: number) => void;
  onView: (product: Product) => void;
};

export function ProductDrawer({ product, related, onClose, onAdd, onView }: Props) {
  const [quantity, setQuantity] = useState(1);
  if (!product) return null;

  return (
    <div className="fixed inset-0 z-50 bg-olive-900/45">
      <aside className="ml-auto flex h-full w-full max-w-xl flex-col bg-cream shadow-panel">
        <div className="flex items-center justify-between border-b border-olive-100 p-4">
          <h2 className="font-display text-2xl text-olive-900">Scheda prodotto</h2>
          <button className="rounded border border-olive-200 p-2 text-olive-900" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          <img src={product.image} alt={product.name} className="h-72 w-full object-cover" />
          <div className="p-5">
            <p className="text-sm font-semibold uppercase tracking-widest text-gold">{product.volume ?? "Selezione Oro Naturale"}</p>
            <h3 className="mt-2 font-display text-3xl leading-tight text-olive-900">{product.name}</h3>
            <p className="mt-3 text-2xl font-bold text-clay">{formatMoney(product.price)}</p>
            <p className="mt-4 leading-7 text-olive-700">{product.description}</p>
            <div className="mt-6 flex items-center gap-3">
              <button className="rounded border border-olive-200 p-3" onClick={() => setQuantity(Math.max(1, quantity - 1))}>
                <Minus size={18} />
              </button>
              <span className="min-w-12 text-center text-lg font-bold">{quantity}</span>
              <button className="rounded border border-olive-200 p-3" onClick={() => setQuantity(quantity + 1)}>
                <Plus size={18} />
              </button>
              <button className="ml-auto rounded bg-olive-900 px-5 py-3 font-bold text-cream" onClick={() => onAdd(product, quantity)}>
                Aggiungi al carrello
              </button>
            </div>
            <div className="mt-8">
              <h4 className="font-bold text-olive-900">Consigliati con questo prodotto</h4>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {related.slice(0, 2).map((item) => (
                  <button key={item.id} className="flex gap-3 rounded border border-olive-100 bg-white p-2 text-left" onClick={() => onView(item)}>
                    <img src={item.image} alt={item.name} className="h-16 w-16 rounded object-cover" />
                    <span className="text-sm font-semibold text-olive-900">{item.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
