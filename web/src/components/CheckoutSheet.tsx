import { useState } from "react";
import { CreditCard, Loader2, ShieldCheck, Wallet } from "lucide-react";
import { localizeProduct, useI18n } from "../i18n";
import type { CartItem, ShippingDetails } from "../types";
import { formatMoney } from "../utils/money";
import { COUNTRIES, shippingFor } from "../utils/shipping";
import { Sheet } from "./Sheet";

export type PayChoice = "revolut" | "paypal";

type Props = {
  open: boolean;
  items: CartItem[];
  subtotal: number;
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
  subtotal,
  defaultName,
  processing,
  error,
  revolutEnabled,
  paypalEnabled,
  onClose,
  onPay,
}: Props) {
  const { lang, t } = useI18n();
  const [name, setName] = useState(defaultName ?? "");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [zip, setZip] = useState("");
  const [country, setCountry] = useState("IT");
  const [notes, setNotes] = useState("");
  const [method, setMethod] = useState<PayChoice>(revolutEnabled ? "revolut" : "paypal");

  const shipping = shippingFor(subtotal, country);
  const total = subtotal + shipping;
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
        country,
        notes: notes.trim() || undefined,
      },
      method,
    );
  }

  return (
    <Sheet open={open} title={t("checkout")} onClose={onClose}>
      <div className="px-5 pb-5">
        <div className="rounded-2xl border border-olive-100 bg-white p-3.5">
          <p className="text-[11px] font-bold uppercase tracking-widest text-gold">{t("summary")}</p>
          <ul className="mt-2 space-y-1 text-[13px] text-olive-700">
            {items.map((item) => (
              <li key={item.product.id} className="flex justify-between gap-3">
                <span className="line-clamp-2">
                  {item.quantity}× {localizeProduct(item.product, lang).name}
                </span>
                <span className="shrink-0 font-bold text-olive-900">
                  {formatMoney(item.product.price * item.quantity)}
                </span>
              </li>
            ))}
          </ul>
          <dl className="mt-2 space-y-1 border-t border-olive-100 pt-2 text-[13px] text-olive-700">
            <div className="flex justify-between">
              <dt>{t("subtotal")}</dt>
              <dd className="font-semibold text-olive-900">{formatMoney(subtotal)}</dd>
            </div>
            <div className="flex justify-between">
              <dt>{t("shipping")}</dt>
              <dd className="font-semibold text-olive-900">
                {shipping === 0 ? t("free") : formatMoney(shipping)}
              </dd>
            </div>
            <div className="flex justify-between border-t border-olive-100 pt-1 text-sm font-extrabold text-olive-900">
              <dt>{t("total")}</dt>
              <dd>{formatMoney(total)}</dd>
            </div>
          </dl>
        </div>

        <p className="mt-4 text-[11px] font-bold uppercase tracking-widest text-gold">{t("shipping")}</p>
        <div className="mt-2 space-y-2.5">
          <input className={inputClass} placeholder={t("fullName")} value={name} disabled={processing} onChange={(e) => setName(e.target.value)} />
          <input className={inputClass} placeholder={t("phone")} type="tel" value={phone} disabled={processing} onChange={(e) => setPhone(e.target.value)} />
          <input className={inputClass} placeholder={t("addressLine")} value={address} disabled={processing} onChange={(e) => setAddress(e.target.value)} />
          <div className="flex gap-2.5">
            <input className={inputClass} placeholder={t("city")} value={city} disabled={processing} onChange={(e) => setCity(e.target.value)} />
            <input className={`${inputClass} max-w-[110px]`} placeholder={t("zip")} inputMode="numeric" value={zip} disabled={processing} onChange={(e) => setZip(e.target.value)} />
          </div>
          <select
            className={inputClass}
            value={country}
            disabled={processing}
            onChange={(e) => setCountry(e.target.value)}
            aria-label={t("country")}
          >
            {COUNTRIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name}
              </option>
            ))}
          </select>
          <input className={inputClass} placeholder={t("notes")} value={notes} disabled={processing} onChange={(e) => setNotes(e.target.value)} />
        </div>

        {!noPayment && (
          <>
            <p className="mt-4 text-[11px] font-bold uppercase tracking-widest text-gold">{t("paymentMethod")}</p>
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
                  {t("cardRevolut")}
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
            {method === "revolut" ? t("secureRevolut") : t("paypalInfo")}
          </div>
        </div>

        {error && (
          <p className="mt-3 rounded-xl bg-clay/10 px-3 py-2 text-center text-[12px] font-bold text-clay">
            {error}
          </p>
        )}
        {noPayment && (
          <p className="mt-3 rounded-xl bg-gold/10 px-3 py-2 text-center text-[12px] font-bold text-clay">
            {t("noPayment")}
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
                {t("processing")}
              </>
            ) : (
              <>{method === "paypal" ? t("payPaypal") : t("pay")} · {formatMoney(total)}</>
            )}
          </button>
        </div>
      </div>
    </Sheet>
  );
}
