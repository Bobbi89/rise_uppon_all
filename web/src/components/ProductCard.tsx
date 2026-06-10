import { Plus, Search } from "lucide-react";
import type { Product } from "../types";
import { formatMoney } from "../utils/money";

type Props = {
  product: Product;
  onAdd: (product: Product, quantity?: number) => void;
  onView: (product: Product) => void;
};

export function ProductCard({ product, onAdd, onView }: Props) {
  return (
    <article className="overflow-hidden rounded border border-olive-100 bg-white shadow-sm">
      <button className="block w-full text-left" onClick={() => onView(product)}>
        <div className="aspect-[4/3] overflow-hidden bg-olive-50">
          <img src={product.image} alt={product.name} className="h-full w-full object-cover transition duration-300 hover:scale-105" />
        </div>
        <div className="p-4">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-base font-bold leading-snug text-olive-900">{product.name}</h3>
            <span className="shrink-0 font-bold text-clay">{formatMoney(product.price)}</span>
          </div>
          <p className="mt-2 line-clamp-2 text-sm leading-6 text-olive-700">{product.description}</p>
        </div>
      </button>
      <div className="flex border-t border-olive-100">
        <button className="inline-flex flex-1 items-center justify-center gap-2 px-3 py-3 text-sm font-bold text-olive-900" onClick={() => onView(product)}>
          <Search size={16} />
          Dettagli
        </button>
        <button className="inline-flex flex-1 items-center justify-center gap-2 bg-olive-900 px-3 py-3 text-sm font-bold text-cream" onClick={() => onAdd(product, 1)}>
          <Plus size={16} />
          Aggiungi
        </button>
      </div>
    </article>
  );
}
