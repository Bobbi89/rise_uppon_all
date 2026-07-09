import { useState } from "react";
import { Apple, CreditCard, Loader2, ShieldCheck, Wallet } from "lucide-react";
import type { CartItem, ShippingDetails } from "../types";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

type Props = {
  open: boolean;
  items: CartItem[];
  total: number;
  defaultName?: string;
  processing: boolean;
  error: string | null;
  revolutEnabled: boolean;
  onClose: () => void;
  onPay: (details: ShippingDetails) => void;
};

const inputClass =
  "w-full rounded-xl border border-olive-100 bg-white px-3.5 py-3 text-sm text-olive-900 placeholder:text-olive-400/60 focus:border-olive-500 focus:outline-none disabled:opacity-60";

/** True se il dispositivo può usare Apple Pay (Safari/iOS con Apple Pay). */
function applePayAvailable(): boolean {
  try {
    const aps = (window as unknown as { ApplePaySession?: { canMakePayments?: () => boolean } }).ApplePaySession;
    return !!aps?.canMakePayments?.();
  } catch {
    return false;
  }
}

export function CheckoutSheet({
  open,
  items,
  total,
  defaultName,
  processing,
  error,
  revolutEnabled,
  onClose,
  onPay,
}: Props) {
  const [name, setName] = useState(defaultName ?? "");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [zip, setZip] = useState("");
  const [notes, setNotes] = useState("");

  const valid = name.trim() && phone.trim() && address.trim() && city.trim() && zip.trim();

  function submit() {
    if (!valid || processing) return;
    onPay({
      name: name.trim(),
      phone: phone.trim(),
      address: address.trim(),
      city: city.trim(),
      zip: zip.trim(),
      notes: notes.trim() || undefined,
    });
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
          <input className={inputClass} placeholder="Nome e cognome" value={name} disabled={processing} onChange={(e) => setName(e.target.value)} />
          <input className={inputClass} placeholder="Telefono" type="tel" value={phone} disabled={processing} onChange={(e) => setPhone(e.target.value)} />
          <input className={inputClass} placeholder="Indirizzo e numero civico" value={address} disabled={processing} onChange={(e) => setAddress(e.target.value)} />
          <div className="flex gap-2.5">
            <input className={inputClass} placeholder="Città" value={city} disabled={processing} onChange={(e) => setCity(e.target.value)} />
            <input className={`${inputClass} max-w-[110px]`} placeholder="CAP" inputMode="numeric" value={zip} disabled={processing} onChange={(e) => setZip(e.target.value)} />
          </div>
          <input className={inputClass} placeholder="Note per il corriere (opzionale)" value={notes} disabled={processing} onChange={(e) => setNotes(e.target.value)} />
        </div>

        <div className="mt-4 flex items-center gap-2 rounded-2xl border border-olive-100 bg-white p-3">
          <ShieldCheck size={18} className="shrink-0 text-olive-500" />
          <div className="text-[12px] leading-4 text-olive-700">
            Pagamento sicuro con <b>Revolut</b>: carta{" "}
            <CreditCard size={12} className="inline align-[-1px]" />, Revolut Pay{" "}
            <Wallet size={12} className="inline align-[-1px]" /> e Apple Pay.
          </div>
        </div>

        {applePayAvailable() && (
          <p className="mt-2 flex items-center justify-center gap-1.5 rounded-2xl bg-olive-900 px-3 py-2 text-[12px] font-bold text-cream">
            <Apple size={14} /> Apple Pay disponibile su questo dispositivo
          </p>
        )}

        {error && (
          <p className="mt-3 rounded-xl bg-clay/10 px-3 py-2 text-center text-[12px] font-bold text-clay">
            {error}
          </p>
        )}
        {!revolutEnabled && (
          <p className="mt-3 rounded-xl bg-gold/10 px-3 py-2 text-center text-[12px] font-bold text-clay">
            Pagamenti non ancora configurati: l'ordine verrà registrato e ti contatteremo.
          </p>
        )}

        <div className="safe-bottom mt-4">
          <button
            disabled={!valid || processing}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-olive-900 py-3.5 text-sm font-extrabold text-cream active:scale-[0.98]"
            onClick={submit}
          >
            {processing ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Elaborazione…
              </>
            ) : (
              <>Paga {formatMoney(total)}</>
            )}
          </button>
        </div>
      </div>
    </Sheet>
  );
}
