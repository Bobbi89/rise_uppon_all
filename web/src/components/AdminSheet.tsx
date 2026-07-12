import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChefHat, Loader2, PackageCheck, Truck, XCircle } from "lucide-react";
import { api } from "../api";
import type { ServerOrder } from "../types";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

type Props = {
  open: boolean;
  onClose: () => void;
};

const STATUS: Record<string, { text: string; className: string }> = {
  pending: { text: "Da pagare", className: "bg-gold/15 text-clay" },
  awaiting_payment: { text: "PayPal da confermare", className: "bg-gold/15 text-clay" },
  paid: { text: "Pagato", className: "bg-olive-100 text-olive-700" },
  preparing: { text: "In preparazione", className: "bg-gold/15 text-clay" },
  shipped: { text: "Spedito", className: "bg-olive-900 text-cream" },
  delivered: { text: "Consegnato", className: "bg-olive-500 text-cream" },
  cancelled: { text: "Annullato", className: "bg-clay/15 text-clay" },
};

type Filter = "all" | "todo" | "shipped" | "done";
const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "Tutti" },
  { id: "todo", label: "Da spedire" },
  { id: "shipped", label: "Spediti" },
  { id: "done", label: "Consegnati" },
];

function fmtDate(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("it-IT", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" });
}

const inputClass =
  "w-full rounded-lg border border-olive-100 bg-white px-2.5 py-2 text-[13px] text-olive-900 placeholder:text-olive-400/60 focus:border-olive-500 focus:outline-none";

function OrderCard({ order, onPatch }: { order: ServerOrder; onPatch: (o: ServerOrder) => void }) {
  const [carrier, setCarrier] = useState(order.tracking_carrier ?? "");
  const [code, setCode] = useState(order.tracking_code ?? "");
  const [url, setUrl] = useState(order.tracking_url ?? "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const badge = STATUS[order.status] ?? { text: order.status, className: "bg-olive-100 text-olive-700" };

  async function saveTracking() {
    if (!carrier.trim() || !code.trim() || busy) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await api.setTracking(order.id, { carrier: carrier.trim(), code: code.trim(), url: url.trim() || undefined });
      onPatch(res.order);
    } catch (e) {
      setErr((e as Error).message || "Errore");
    } finally {
      setBusy(false);
    }
  }

  async function setStatus(status: string) {
    if (busy) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await api.setStatus(order.id, status);
      onPatch(res.order);
    } catch (e) {
      setErr((e as Error).message || "Errore");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl border border-olive-100 bg-white p-3.5">
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[12px] font-bold text-olive-900">#{order.id}</span>
        <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${badge.className}`}>{badge.text}</span>
      </div>

      <div className="mt-1 flex items-center justify-between text-[12px] text-olive-400">
        <span>{fmtDate(order.created_at)}</span>
        <span className="text-sm font-extrabold text-olive-900">{formatMoney(order.total)}</span>
      </div>

      <p className="mt-1.5 text-[12px] font-bold text-olive-900">
        {order.shipping_name || "—"} · {order.shipping_phone || "—"}
      </p>
      <p className="text-[12px] text-olive-700">
        {order.shipping_address}, {order.shipping_zip} {order.shipping_city}
      </p>

      <ul className="mt-1.5 border-t border-olive-100 pt-1.5 text-[12px] text-olive-700">
        {order.items.map((it, idx) => (
          <li key={idx} className="flex justify-between gap-2">
            <span>{it.quantity}× {it.name}</span>
            <span className="font-semibold text-olive-900">{formatMoney(it.price * it.quantity)}</span>
          </li>
        ))}
      </ul>

      <p className="mt-1 text-[11px] text-olive-400">
        Pagamento: {order.payment_method || "—"}
        {order.paid_at ? ` · pagato il ${fmtDate(order.paid_at)}` : ""}
      </p>

      {/* Azioni stato */}
      <div className="mt-2 flex flex-wrap gap-1.5">
        {order.status === "awaiting_payment" && (
          <button onClick={() => setStatus("paid")} disabled={busy}
            className="flex items-center gap-1 rounded-full bg-olive-900 px-2.5 py-1 text-[11px] font-bold text-cream active:scale-95">
            <CheckCircle2 size={12} /> Segna pagato
          </button>
        )}
        <button onClick={() => setStatus("preparing")} disabled={busy}
          className="flex items-center gap-1 rounded-full bg-olive-100 px-2.5 py-1 text-[11px] font-bold text-olive-700 active:scale-95">
          <ChefHat size={12} /> Preparazione
        </button>
        <button onClick={() => setStatus("delivered")} disabled={busy}
          className="flex items-center gap-1 rounded-full bg-olive-100 px-2.5 py-1 text-[11px] font-bold text-olive-700 active:scale-95">
          <CheckCircle2 size={12} /> Consegnato
        </button>
        <button onClick={() => setStatus("cancelled")} disabled={busy}
          className="flex items-center gap-1 rounded-full bg-clay/10 px-2.5 py-1 text-[11px] font-bold text-clay active:scale-95">
          <XCircle size={12} /> Annulla
        </button>
      </div>

      {/* Spedizione / tracking */}
      <div className="mt-2 space-y-2 rounded-xl bg-olive-50 p-2.5">
        <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-gold">
          <Truck size={13} /> Spedizione
        </p>
        <div className="flex gap-2">
          <input className={inputClass} placeholder="Corriere (BRT…)" value={carrier} onChange={(e) => setCarrier(e.target.value)} />
          <input className={inputClass} placeholder="Codice tracking" value={code} onChange={(e) => setCode(e.target.value)} />
        </div>
        <input className={inputClass} placeholder="URL tracking (opzionale)" value={url} onChange={(e) => setUrl(e.target.value)} />
        {err && <p className="text-[12px] font-bold text-clay">{err}</p>}
        <button onClick={saveTracking} disabled={!carrier.trim() || !code.trim() || busy}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-olive-900 py-2 text-[13px] font-bold text-cream active:scale-[0.98]">
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Truck size={14} />}
          {order.tracking_code ? "Aggiorna tracking" : "Invia tracking al cliente"}
        </button>
      </div>
    </div>
  );
}

export function AdminSheet({ open, onClose }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orders, setOrders] = useState<ServerOrder[]>([]);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    setFilter("all");
    api
      .adminOrders()
      .then((data) => setOrders(data.orders))
      .catch((e) => setError(e.message || "Errore"))
      .finally(() => setLoading(false));
  }, [open]);

  function patch(updated: ServerOrder) {
    setOrders((cur) => cur.map((o) => (o.id === updated.id ? updated : o)));
  }

  const stats = useMemo(() => {
    const paid = orders.filter(
      (o) => o.status !== "pending" && o.status !== "awaiting_payment" && o.status !== "cancelled",
    );
    const revenue = paid.reduce((s, o) => s + o.total, 0);
    const toShip = orders.filter((o) => o.status === "paid" || o.status === "preparing").length;
    return { total: orders.length, revenue, toShip };
  }, [orders]);

  const shown = useMemo(() => {
    switch (filter) {
      case "todo":
        return orders.filter((o) => o.status === "paid" || o.status === "preparing");
      case "shipped":
        return orders.filter((o) => o.status === "shipped");
      case "done":
        return orders.filter((o) => o.status === "delivered");
      default:
        return orders;
    }
  }, [orders, filter]);

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
          <>
            {/* Statistiche */}
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-xl bg-white p-2.5 text-center shadow-card">
                <p className="text-lg font-extrabold text-olive-900">{stats.total}</p>
                <p className="text-[11px] font-semibold text-olive-400">Ordini</p>
              </div>
              <div className="rounded-xl bg-white p-2.5 text-center shadow-card">
                <p className="text-lg font-extrabold text-clay">{stats.toShip}</p>
                <p className="text-[11px] font-semibold text-olive-400">Da spedire</p>
              </div>
              <div className="rounded-xl bg-white p-2.5 text-center shadow-card">
                <p className="text-lg font-extrabold text-olive-900">{formatMoney(stats.revenue)}</p>
                <p className="text-[11px] font-semibold text-olive-400">Incasso</p>
              </div>
            </div>

            {/* Filtri */}
            <div className="no-scrollbar mt-3 flex gap-2 overflow-x-auto pb-1">
              {FILTERS.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setFilter(f.id)}
                  className={`shrink-0 rounded-full px-3 py-1.5 text-[12px] font-bold ${
                    filter === f.id ? "bg-olive-900 text-cream" : "border border-olive-100 bg-white text-olive-700"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {shown.length === 0 ? (
              <div className="py-10 text-center">
                <PackageCheck size={40} className="mx-auto text-olive-200" />
                <p className="mt-3 text-sm font-semibold text-olive-700">Nessun ordine in questa vista.</p>
              </div>
            ) : (
              <div className="mt-3 space-y-3">
                {shown.map((order) => (
                  <OrderCard key={order.id} order={order} onPatch={patch} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </Sheet>
  );
}
