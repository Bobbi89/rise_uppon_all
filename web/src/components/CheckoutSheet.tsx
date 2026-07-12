import { useState } from "react";
import { CreditCard, Loader2, ShieldCheck, Wallet } from "lucide-react";
import type { CartItem, ShippingDetails } from "../types";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

export type PayChoice = "revolut" | "paypal";

type Props = {
  open: boolean;
  items: CartItem[];
  total: number;
  defaultName?: string;
  processing: boolean;
  error: string | null;
  revolutEnabled: boolean;
  paypalEnabled: boolean;
  onClose: () => void;
  onPay: (details: ShippingDetails, method: PayChoice) => void;
};

const inputClass =
  "w-full rounded-xl border border-olive-100 bg-white px-3.5 py-3 text-sm text-olive-900 placeholder:text-olive-400/60 focus:border-olive-500 focus:outline-none disabled:opacity-60";

export function CheckoutSheet({
  open,
  items,
  total,
  defaultName,
  processing,
  error,
  revolutEnabled,
  paypalEnabled,
  onClose,
  onPay,
}: Props) {
  const [name, setName] = useState(defaultName ?? "");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [zip, setZip] = useState("");
  const [notes, setNotes] = useState("");
  const [method, setMethod] = useState<PayChoice>(revolutEnabled ? "revolut" : "paypal");

  const valid = name.trim() && phone.trim() && address.trim() && city.trim() && zip.trim();
  const noPayment = !revolutEnabled && !paypalEnabled;

  function submit() {
    if (!valid || processing) return;
    onPay(
      {
        name: name.trim(),
        phone: phone.trim(),
        address: address.trim(),
        city: city.trim(),
        zip: zip.trim(),
        notes: notes.trim() || undefined,
      },
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
          <input className={inputClass} placeholder="Nome e cognome" value={name} disabled={processing} onChange={(e) => setName(e.target.value)} />
          <input className={inputClass} placeholder="Telefono" type="tel" value={phone} disabled={processing} onChange={(e) => setPhone(e.target.value)} />
          <input className={inputClass} placeholder="Indirizzo e numero civico" value={address} disabled={processing} onChange={(e) => setAddress(e.target.value)} />
          <div className="flex gap-2.5">
            <input className={inputClass} placeholder="Città" value={city} disabled={processing} onChange={(e) => setCity(e.target.value)} />
            <input className={`${inputClass} max-w-[110px]`} placeholder="CAP" inputMode="numeric" value={zip} disabled={processing} onChange={(e) => setZip(e.target.value)} />
          </div>
          <input className={inputClass} placeholder="Note per il corriere (opzionale)" value={notes} disabled={processing} onChange={(e) => setNotes(e.target.value)} />
        </div>

        {!noPayment && (
          <>
            <p className="mt-4 text-[11px] font-bold uppercase tracking-widest text-gold">Metodo di pagamento</p>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {revolutEnabled && (
                <button
                  disabled={processing}
                  onClick={() => setMethod("revolut")}
                  className={`flex flex-col items-center gap-1 rounded-2xl border px-2 py-3 text-[12px] font-bold ${
                    method === "revolut" ? "border-olive-900 bg-olive-900 text-cream" : "border-olive-100 bg-white text-olive-700"
                  }`}
                >
                  <CreditCard size={18} />
                  Carta / Revolut Pay
                </button>
              )}
              {paypalEnabled && (
                <button
                  disabled={processing}
                  onClick={() => setMethod("paypal")}
                  className={`flex flex-col items-center gap-1 rounded-2xl border px-2 py-3 text-[12px] font-bold ${
                    method === "paypal" ? "border-olive-900 bg-olive-900 text-cream" : "border-olive-100 bg-white text-olive-700"
                  }`}
                >
                  <Wallet size={18} />
                  PayPal
                </button>
              )}
            </div>
          </>
        )}

        <div className="mt-3 flex items-center gap-2 rounded-2xl border border-olive-100 bg-white p-3">
          <ShieldCheck size={18} className="shrink-0 text-olive-500" />
          <div className="text-[12px] leading-4 text-olive-700">
            {method === "revolut"
              ? "Pagamento sicuro con Revolut (carta o Revolut Pay)."
              : "Con PayPal riceverai le istruzioni per pagare; l'ordine viene confermato alla ricezione."}
          </div>
        </div>

        {error && (
          <p className="mt-3 rounded-xl bg-clay/10 px-3 py-2 text-center text-[12px] font-bold text-clay">
            {error}
          </p>
        )}
        {noPayment && (
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
              <>{method === "paypal" ? "Ordina e paga con PayPal" : "Paga"} · {formatMoney(total)}</>
            )}
          </button>
        </div>
      </div>
    </Sheet>
  );
}
