import { useEffect, useState } from "react";
import { Loader2, MapPin, Package, Trash2, Truck } from "lucide-react";
import { api } from "../api";
import type { ServerOrder } from "../types";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

type Props = {
  open: boolean;
  onClose: () => void;
};

const STATUS_LABEL: Record<string, { text: string; className: string }> = {
  pending: { text: "Da pagare", className: "bg-gold/15 text-clay" },
  awaiting_payment: { text: "PayPal in attesa", className: "bg-gold/15 text-clay" },
  paid: { text: "Pagato", className: "bg-olive-100 text-olive-700" },
  preparing: { text: "In preparazione", className: "bg-olive-100 text-olive-700" },
  shipped: { text: "Spedito", className: "bg-olive-900 text-cream" },
  delivered: { text: "Consegnato", className: "bg-olive-900 text-cream" },
  cancelled: { text: "Annullato", className: "bg-clay/15 text-clay" },
};

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_LABEL[status] ?? { text: status, className: "bg-olive-100 text-olive-700" };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${s.className}`}>{s.text}</span>
  );
}

export function ProfileSheet({ open, onClose }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orders, setOrders] = useState<ServerOrder[]>([]);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    api
      .getProfile()
      .then((data) => setOrders(data.orders))
      .catch((e) => setError(e.message || "Errore nel caricamento"))
      .finally(() => setLoading(false));
  }, [open]);

  const pendingCount = orders.filter((o) => o.status === "pending").length;

  async function clearPending() {
    if (clearing) return;
    setClearing(true);
    try {
      const res = await api.clearPending();
      setOrders(res.orders);
    } catch (e) {
      setError((e as Error).message || "Errore");
    } finally {
      setClearing(false);
    }
  }

  return (
    <Sheet open={open} title="I miei ordini" onClose={onClose}>
      <div className="px-5 pb-6">
        {loading && (
          <div className="flex items-center justify-center gap-2 py-10 text-sm text-olive-700">
            <Loader2 size={18} className="animate-spin" /> Caricamento…
          </div>
        )}

        {error && !loading && (
          <p className="rounded-xl bg-clay/10 px-3 py-2 text-center text-[13px] font-bold text-clay">{error}</p>
        )}

        {!loading && !error && orders.length === 0 && (
          <div className="py-10 text-center">
            <Package size={40} className="mx-auto text-olive-200" />
            <p className="mt-3 text-sm font-semibold text-olive-700">Non hai ancora ordini.</p>
          </div>
        )}

        {!loading && pendingCount > 0 && (
          <button
            onClick={clearPending}
            disabled={clearing}
            className="mb-3 flex w-full items-center justify-center gap-1.5 rounded-xl border border-clay/30 bg-clay/5 py-2.5 text-[12px] font-bold text-clay active:scale-[0.99]"
          >
            {clearing ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
            Svuota ordini non pagati ({pendingCount})
          </button>
        )}

        <div className="space-y-3">
          {orders.map((order) => (
            <div key={order.id} className="rounded-2xl border border-olive-100 bg-white p-3.5">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[12px] font-bold text-olive-900">#{order.id}</span>
                <StatusBadge status={order.status} />
              </div>
              <ul className="mt-2 space-y-0.5 text-[13px] text-olive-700">
                {order.items.map((it, idx) => (
                  <li key={idx} className="flex justify-between gap-3">
                    <span className="line-clamp-1">
                      {it.quantity}× {it.name}
                    </span>
                    <span className="shrink-0 font-semibold text-olive-900">
                      {formatMoney(it.price * it.quantity)}
                    </span>
                  </li>
                ))}
              </ul>
              <div className="mt-2 flex items-center justify-between border-t border-olive-100 pt-2 text-sm">
                <span className="text-olive-700">Totale</span>
                <span className="font-extrabold text-olive-900">{formatMoney(order.total)}</span>
              </div>

              {(order.shipping_address || order.shipping_city) && (
                <p className="mt-2 flex items-start gap-1.5 text-[12px] text-olive-700">
                  <MapPin size={13} className="mt-0.5 shrink-0" />
                  {order.shipping_address}, {order.shipping_zip} {order.shipping_city}
                </p>
              )}

              {order.tracking_code ? (
                <div className="mt-2 rounded-xl bg-olive-50 px-3 py-2 text-[12px]">
                  <p className="flex items-center gap-1.5 font-bold text-olive-900">
                    <Truck size={14} /> Spedito con {order.tracking_carrier}
                  </p>
                  <p className="mt-0.5 text-olive-700">
                    Codice: <span className="font-mono font-bold">{order.tracking_code}</span>
                  </p>
                  {order.tracking_url && (
                    <a
                      href={order.tracking_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 inline-block font-bold text-clay underline"
                    >
                      Traccia la spedizione →
                    </a>
                  )}
                </div>
              ) : (
                order.status === "paid" && (
                  <p className="mt-2 text-[12px] font-semibold text-olive-400">
                    In preparazione — riceverai il codice di tracking qui.
                  </p>
                )
              )}
            </div>
          ))}
        </div>
      </div>
    </Sheet>
  );
}
