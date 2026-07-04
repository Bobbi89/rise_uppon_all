import { useEffect, useState } from "react";
import { Loader2, PackageCheck, Truck } from "lucide-react";
import { api } from "../api";
import type { ServerOrder } from "../types";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

type Props = {
  open: boolean;
  onClose: () => void;
};

const inputClass =
  "w-full rounded-lg border border-olive-100 bg-white px-2.5 py-2 text-[13px] text-olive-900 placeholder:text-olive-400/60 focus:border-olive-500 focus:outline-none";

function TrackingForm({ order, onSaved }: { order: ServerOrder; onSaved: (o: ServerOrder) => void }) {
  const [carrier, setCarrier] = useState(order.tracking_carrier ?? "");
  const [code, setCode] = useState(order.tracking_code ?? "");
  const [url, setUrl] = useState(order.tracking_url ?? "");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function save() {
    if (!carrier.trim() || !code.trim() || saving) return;
    setSaving(true);
    setErr(null);
    try {
      const res = await api.setTracking(order.id, {
        carrier: carrier.trim(),
        code: code.trim(),
        url: url.trim() || undefined,
      });
      onSaved(res.order);
    } catch (e) {
      setErr((e as Error).message || "Errore");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-2 space-y-2 rounded-xl bg-olive-50 p-2.5">
      <div className="flex gap-2">
        <input className={inputClass} placeholder="Corriere (BRT…)" value={carrier} onChange={(e) => setCarrier(e.target.value)} />
        <input className={inputClass} placeholder="Codice tracking" value={code} onChange={(e) => setCode(e.target.value)} />
      </div>
      <input className={inputClass} placeholder="URL tracking (opzionale)" value={url} onChange={(e) => setUrl(e.target.value)} />
      {err && <p className="text-[12px] font-bold text-clay">{err}</p>}
      <button
        disabled={!carrier.trim() || !code.trim() || saving}
        onClick={save}
        className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-olive-900 py-2 text-[13px] font-bold text-cream active:scale-[0.98]"
      >
        {saving ? <Loader2 size={14} className="animate-spin" /> : <Truck size={14} />}
        {order.tracking_code ? "Aggiorna tracking" : "Invia tracking al cliente"}
      </button>
    </div>
  );
}

export function AdminSheet({ open, onClose }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orders, setOrders] = useState<ServerOrder[]>([]);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    api
      .adminOrders()
      .then((data) => setOrders(data.orders))
      .catch((e) => setError(e.message || "Errore"))
      .finally(() => setLoading(false));
  }, [open]);

  function patchOrder(updated: ServerOrder) {
    setOrders((cur) => cur.map((o) => (o.id === updated.id ? updated : o)));
  }

  const paidCount = orders.filter((o) => o.status !== "pending").length;

  return (
    <Sheet open={open} title="Gestione ordini (Admin)" onClose={onClose}>
      <div className="px-5 pb-6">
        {loading && (
          <div className="flex items-center justify-center gap-2 py-10 text-sm text-olive-700">
            <Loader2 size={18} className="animate-spin" /> Caricamento…
          </div>
        )}
        {error && !loading && (
          <p className="rounded-xl bg-clay/10 px-3 py-2 text-center text-[13px] font-bold text-clay">{error}</p>
        )}

        {!loading && !error && (
          <p className="mb-3 flex items-center gap-1.5 text-[12px] font-semibold text-olive-400">
            <PackageCheck size={14} /> {orders.length} ordini · {paidCount} pagati
          </p>
        )}

        <div className="space-y-3">
          {orders.map((order) => (
            <div key={order.id} className="rounded-2xl border border-olive-100 bg-white p-3.5">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[12px] font-bold text-olive-900">#{order.id}</span>
                <span className="text-sm font-extrabold text-olive-900">{formatMoney(order.total)}</span>
              </div>
              <p className="mt-1 text-[12px] text-olive-700">
                {order.shipping_name} · {order.shipping_phone}
              </p>
              <p className="text-[12px] text-olive-700">
                {order.shipping_address}, {order.shipping_zip} {order.shipping_city}
              </p>
              <ul className="mt-1.5 text-[12px] text-olive-700">
                {order.items.map((it, idx) => (
                  <li key={idx}>
                    {it.quantity}× {it.name}
                  </li>
                ))}
              </ul>
              <p className="mt-1 text-[12px] font-bold text-olive-900">
                Stato: {order.status}
                {order.payment_method ? ` · ${order.payment_method}` : ""}
              </p>
              <TrackingForm order={order} onSaved={patchOrder} />
            </div>
          ))}
        </div>
      </div>
    </Sheet>
  );
}
