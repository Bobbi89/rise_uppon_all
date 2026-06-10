import { CreditCard, Landmark } from "lucide-react";
import { useState } from "react";
import type { CartItem, PaymentMethod, ShippingDetails } from "../types";
import { formatMoney } from "../utils/money";

type Props = {
  items: CartItem[];
  total: number;
  onConfirm: (details: ShippingDetails, method: PaymentMethod) => void;
};

export function CheckoutForm({ items, total, onConfirm }: Props) {
  const [method, setMethod] = useState<PaymentMethod>("revolut");
  const [details, setDetails] = useState<ShippingDetails>({
    name: "",
    email: "",
    address: "",
    city: "",
    country: "Italia",
  });

  const canSubmit = items.length > 0 && details.name && details.email && details.address && details.city;

  return (
    <section id="checkout" className="bg-white py-12">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 lg:grid-cols-[1fr_420px]">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-gold">Checkout</p>
          <h2 className="mt-2 font-display text-4xl text-olive-900">Pagamento e spedizione</h2>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {(["stripe", "revolut"] as PaymentMethod[]).map((item) => {
              const Icon = item === "stripe" ? CreditCard : Landmark;
              return (
                <button
                  key={item}
                  className={`flex items-center gap-3 rounded border p-4 text-left ${
                    method === item ? "border-olive-900 bg-olive-50" : "border-olive-100 bg-white"
                  }`}
                  onClick={() => setMethod(item)}
                >
                  <Icon size={22} />
                  <span>
                    <span className="block font-bold text-olive-900">{item === "stripe" ? "Stripe" : "Revolut Pay"}</span>
                    <span className="text-sm text-olive-700">Pagamento carta sicuro</span>
                  </span>
                </button>
              );
            })}
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <input className="rounded border border-olive-200 px-4 py-3" placeholder="Nome e cognome" value={details.name} onChange={(e) => setDetails({ ...details, name: e.target.value })} />
            <input className="rounded border border-olive-200 px-4 py-3" placeholder="Email" value={details.email} onChange={(e) => setDetails({ ...details, email: e.target.value })} />
            <input className="rounded border border-olive-200 px-4 py-3 sm:col-span-2" placeholder="Indirizzo completo" value={details.address} onChange={(e) => setDetails({ ...details, address: e.target.value })} />
            <input className="rounded border border-olive-200 px-4 py-3" placeholder="Citta" value={details.city} onChange={(e) => setDetails({ ...details, city: e.target.value })} />
            <input className="rounded border border-olive-200 px-4 py-3" placeholder="Paese" value={details.country} onChange={(e) => setDetails({ ...details, country: e.target.value })} />
          </div>
        </div>
        <aside className="rounded border border-olive-100 bg-cream p-5">
          <h3 className="font-bold text-olive-900">Riepilogo ordine</h3>
          <div className="mt-4 space-y-3">
            {items.map((item) => (
              <div key={item.product.id} className="flex justify-between gap-3 text-sm">
                <span>{item.product.name} x{item.quantity}</span>
                <strong>{formatMoney(item.product.price * item.quantity)}</strong>
              </div>
            ))}
          </div>
          <div className="mt-5 border-t border-olive-200 pt-4">
            <div className="flex justify-between text-lg text-olive-900">
              <span>Totale</span>
              <strong>{formatMoney(total)}</strong>
            </div>
          </div>
          <button className="mt-5 w-full rounded bg-clay px-5 py-3 font-bold text-white disabled:opacity-50" disabled={!canSubmit} onClick={() => onConfirm(details, method)}>
            Conferma e genera ordine
          </button>
        </aside>
      </div>
    </section>
  );
}
