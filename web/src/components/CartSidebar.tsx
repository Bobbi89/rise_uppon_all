import { Minus, Plus, Trash2, X } from "lucide-react";
import type { CartItem } from "../types";
import { formatMoney } from "../utils/money";

type Props = {
  open: boolean;
  items: CartItem[];
  subtotal: number;
  shipping: number;
  total: number;
  onClose: () => void;
  onUpdate: (productId: string, quantity: number) => void;
  onRemove: (productId: string) => void;
  onClear: () => void;
  onCheckout: () => void;
};

export function CartSidebar({ open, items, subtotal, shipping, total, onClose, onUpdate, onRemove, onClear, onCheckout }: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-olive-900/45">
      <aside className="ml-auto flex h-full w-full max-w-lg flex-col bg-cream shadow-panel">
        <div className="flex items-center justify-between border-b border-olive-100 p-4">
          <h2 className="font-display text-2xl text-olive-900">Carrello</h2>
          <button className="rounded border border-olive-200 p-2" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {items.length === 0 ? (
            <p className="rounded border border-olive-100 bg-white p-4 text-olive-700">Il carrello e` vuoto.</p>
          ) : (
            <div className="space-y-3">
              {items.map((item) => (
                <div key={item.product.id} className="grid grid-cols-[72px_1fr] gap-3 rounded border border-olive-100 bg-white p-3">
                  <img src={item.product.image} alt={item.product.name} className="h-20 w-20 rounded object-cover" />
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="font-bold leading-snug text-olive-900">{item.product.name}</h3>
                      <button className="text-clay" onClick={() => onRemove(item.product.id)}>
                        <Trash2 size={17} />
                      </button>
                    </div>
                    <p className="mt-1 text-sm text-olive-700">{formatMoney(item.product.price)}</p>
                    <div className="mt-3 flex items-center gap-2">
                      <button className="rounded border border-olive-200 p-2" onClick={() => onUpdate(item.product.id, item.quantity - 1)}>
                        <Minus size={14} />
                      </button>
                      <span className="w-8 text-center font-bold">{item.quantity}</span>
                      <button className="rounded border border-olive-200 p-2" onClick={() => onUpdate(item.product.id, item.quantity + 1)}>
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="border-t border-olive-100 bg-white p-4">
          <div className="space-y-2 text-sm text-olive-800">
            <div className="flex justify-between"><span>Subtotale</span><strong>{formatMoney(subtotal)}</strong></div>
            <div className="flex justify-between"><span>Spedizione stimata</span><strong>{shipping === 0 ? "Gratis" : formatMoney(shipping)}</strong></div>
            <div className="flex justify-between text-lg text-olive-900"><span>Totale</span><strong>{formatMoney(total)}</strong></div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2">
            <button className="rounded border border-olive-200 px-4 py-3 font-bold text-olive-900" onClick={onClear}>
              Svuota
            </button>
            <button className="rounded bg-olive-900 px-4 py-3 font-bold text-cream disabled:opacity-50" onClick={onCheckout} disabled={!items.length}>
              Checkout
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
}
