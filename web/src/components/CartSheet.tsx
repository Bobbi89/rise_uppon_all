import { Minus, Plus, Trash2 } from "lucide-react";
import type { CartItem } from "../types";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

type Props = {
  open: boolean;
  items: CartItem[];
  subtotal: number;
  shipping: number;
  total: number;
  freeShippingMin: number;
  onClose: () => void;
  onUpdate: (productId: string, quantity: number) => void;
  onCheckout: () => void;
};

export function CartSheet({
  open,
  items,
  subtotal,
  shipping,
  total,
  freeShippingMin,
  onClose,
  onUpdate,
  onCheckout,
}: Props) {
  const missingForFree = Math.max(0, freeShippingMin - subtotal);

  return (
    <Sheet open={open} title="Il tuo carrello" onClose={onClose}>
      {items.length === 0 ? (
        <div className="px-5 pb-10 pt-6 text-center">
          <p className="text-4xl">🛒</p>
          <p className="mt-3 text-sm font-semibold text-olive-700">
            Il carrello è vuoto. Scopri i nostri prodotti biologici!
          </p>
        </div>
      ) : (
        <div className="px-5 pb-5">
          <ul className="divide-y divide-olive-100">
            {items.map((item) => (
              <li key={item.product.id} className="flex items-center gap-3 py-3">
                <img
                  src={item.product.image}
                  alt={item.product.name}
                  className="h-14 w-14 shrink-0 rounded-xl border border-olive-100 object-cover"
                />
                <div className="min-w-0 flex-1">
                  <p className="line-clamp-2 text-[13px] font-bold leading-4 text-olive-900">
                    {item.product.name}
                  </p>
                  <p className="mt-1 text-sm font-extrabold text-olive-900">
                    {formatMoney(item.product.price * item.quantity)}
                  </p>
                </div>
                <div className="flex items-center gap-1 rounded-full border border-olive-100 bg-white p-0.5">
                  <button
                    aria-label="Diminuisci"
                    className="grid h-7 w-7 place-items-center rounded-full text-olive-700"
                    onClick={() => onUpdate(item.product.id, item.quantity - 1)}
                  >
                    {item.quantity === 1 ? <Trash2 size={13} /> : <Minus size={13} />}
                  </button>
                  <span className="w-5 text-center text-[13px] font-extrabold text-olive-900">
                    {item.quantity}
                  </span>
                  <button
                    aria-label="Aumenta"
                    className="grid h-7 w-7 place-items-center rounded-full text-olive-700"
                    onClick={() => onUpdate(item.product.id, item.quantity + 1)}
                  >
                    <Plus size={13} />
                  </button>
                </div>
              </li>
            ))}
          </ul>

          {missingForFree > 0 ? (
            <p className="mt-2 rounded-xl bg-gold/10 px-3 py-2 text-center text-[12px] font-bold text-clay">
              Aggiungi {formatMoney(missingForFree)} per la spedizione gratuita 🚚
            </p>
          ) : (
            <p className="mt-2 rounded-xl bg-olive-100 px-3 py-2 text-center text-[12px] font-bold text-olive-700">
              🎉 Spedizione gratuita sbloccata!
            </p>
          )}

          <dl className="mt-3 space-y-1.5 text-sm text-olive-700">
            <div className="flex justify-between">
              <dt>Subtotale</dt>
              <dd className="font-bold text-olive-900">{formatMoney(subtotal)}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Spedizione</dt>
              <dd className="font-bold text-olive-900">
                {shipping === 0 ? "Gratis" : formatMoney(shipping)}
              </dd>
            </div>
            <div className="flex justify-between border-t border-olive-100 pt-2 text-base">
              <dt className="font-bold text-olive-900">Totale</dt>
              <dd className="font-extrabold text-olive-900">{formatMoney(total)}</dd>
            </div>
          </dl>

          <div className="safe-bottom mt-4">
            <button
              className="w-full rounded-full bg-olive-900 py-3.5 text-sm font-extrabold text-cream active:scale-[0.98]"
              onClick={onCheckout}
            >
              Procedi al checkout · {formatMoney(total)}
            </button>
          </div>
        </div>
      )}
    </Sheet>
  );
}
