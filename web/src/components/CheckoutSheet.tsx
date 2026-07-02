import { useState } from "react";
import { Banknote, CreditCard, Wallet } from "lucide-react";
import type { CartItem, PaymentMethod, ShippingDetails } from "../types";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

type Props = {
  open: boolean;
  items: CartItem[];
  total: number;
  defaultName?: string;
  onClose: () => void;
  onConfirm: (details: ShippingDetails, method: PaymentMethod) => void;
};

const paymentOptions: Array<{ id: PaymentMethod; label: string; icon: typeof CreditCard }> = [
  { id: "stripe", label: "Carta (Stripe)", icon: CreditCard },
  { id: "revolut", label: "Revolut Pay", icon: Wallet },
  { id: "bonifico", label: "Bonifico", icon: Banknote },
];

const inputClass =
  "w-full rounded-xl border border-olive-100 bg-white px-3.5 py-3 text-sm text-olive-900 placeholder:text-olive-400/60 focus:border-olive-500 focus:outline-none";

export function CheckoutSheet({ open, items, total, defaultName, onClose, onConfirm }: Props) {
  const [name, setName] = useState(defaultName ?? "");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [zip, setZip] = useState("");
  const [notes, setNotes] = useState("");
  const [method, setMethod] = useState<PaymentMethod>("stripe");

  const valid = name.trim() && phone.trim() && address.trim() && city.trim() && zip.trim();

  function submit() {
    if (!valid) return;
    onConfirm(
      { name: name.trim(), phone: phone.trim(), address: address.trim(), city: city.trim(), zip: zip.trim(), notes: notes.trim() || undefined },
      method,
    );
  }

  return (
    <Sheet open={open} title="Checkout" onClose={onClose}>
      <div className="px-5 pb-5">
        <div className="rounded-2xl border border-olive-100 bg-white p-3.5">
          <p className="text-[11px] font-bold uppercase tracking-widest text-gold">Riepilogo</p>
          <ul className="mt-2 space-y-1 text-[13px] text-olive-700">
            {items.map((item) => (
              <li key={item.product.id} className="flex justify-between gap-3">
                <span className="line-clamp-2">
                  {item.quantity}× {item.product.name}
                </span>
                <span className="shrink-0 font-bold text-olive-900">
                  {formatMoney(item.product.price * item.quantity)}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-2 flex justify-between border-t border-olive-100 pt-2 text-sm font-extrabold text-olive-900">
            <span>Totale</span>
            <span>{formatMoney(total)}</span>
          </p>
        </div>

        <p className="mt-4 text-[11px] font-bold uppercase tracking-widest text-gold">Spedizione</p>
        <div className="mt-2 space-y-2.5">
          <input className={inputClass} placeholder="Nome e cognome" value={name} onChange={(e) => setName(e.target.value)} />
          <input className={inputClass} placeholder="Telefono" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <input className={inputClass} placeholder="Indirizzo e numero civico" value={address} onChange={(e) => setAddress(e.target.value)} />
          <div className="flex gap-2.5">
            <input className={inputClass} placeholder="Città" value={city} onChange={(e) => setCity(e.target.value)} />
            <input className={`${inputClass} max-w-[110px]`} placeholder="CAP" inputMode="numeric" value={zip} onChange={(e) => setZip(e.target.value)} />
          </div>
          <input className={inputClass} placeholder="Note per il corriere (opzionale)" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>

        <p className="mt-4 text-[11px] font-bold uppercase tracking-widest text-gold">Pagamento</p>
        <div className="mt-2 grid grid-cols-3 gap-2">
          {paymentOptions.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setMethod(id)}
              className={`flex flex-col items-center gap-1.5 rounded-2xl border px-2 py-3 text-[11px] font-bold leading-tight ${
                method === id
                  ? "border-olive-900 bg-olive-900 text-cream"
                  : "border-olive-100 bg-white text-olive-700"
              }`}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </div>

        <div className="safe-bottom mt-5">
          <button
            disabled={!valid}
            className="w-full rounded-full bg-olive-900 py-3.5 text-sm font-extrabold text-cream active:scale-[0.98]"
            onClick={submit}
          >
            Conferma ordine · {formatMoney(total)}
          </button>
          <p className="mt-2 text-center text-[11px] text-olive-400">
            Riceverai la conferma e il link di pagamento direttamente in chat.
          </p>
        </div>
      </div>
    </Sheet>
  );
}
