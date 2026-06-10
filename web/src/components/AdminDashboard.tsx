import { ClipboardCheck, CreditCard, PackageOpen, TimerReset, Truck } from "lucide-react";
import type { Order, Product } from "../types";
import { formatMoney } from "../utils/money";
import { StatusBadge } from "./StatusBadge";

type Props = {
  orders: Order[];
  products: Product[];
};

export function AdminDashboard({ orders, products }: Props) {
  const paid = orders.filter((order) => order.status !== "da pagare").length;
  const pending = orders.filter((order) => order.status === "da pagare" || order.status === "in preparazione").length;
  const shipped = orders.filter((order) => order.status === "spedito").length;
  const revenue = orders.reduce((sum, order) => sum + order.total, 0);
  const stats = [
    { label: "Ordini totali", value: orders.length, icon: ClipboardCheck },
    { label: "Da effettuare", value: pending, icon: TimerReset },
    { label: "Spediti", value: shipped, icon: Truck },
    { label: "Pagamenti", value: paid, icon: CreditCard },
  ];

  return (
    <section id="admin" className="bg-olive-900 py-12 text-cream">
      <div className="mx-auto max-w-7xl px-4">
        <p className="text-sm font-semibold uppercase tracking-widest text-gold">Dashboard admin</p>
        <h2 className="mt-2 font-display text-4xl">Ordini e operazioni</h2>
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map(({ label, value, icon: Icon }) => (
            <div key={label} className="rounded border border-cream/15 bg-white/8 p-4">
              <Icon size={22} className="text-gold" />
              <p className="mt-4 text-3xl font-bold">{value}</p>
              <p className="text-sm text-cream/70">{label}</p>
            </div>
          ))}
        </div>
        <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded border border-cream/15 bg-white/8 p-4">
            <h3 className="font-bold">Tutti gli ordini</h3>
            <div className="mt-4 space-y-3">
              {orders.map((order) => (
                <div key={order.id} className="grid gap-2 rounded bg-cream p-3 text-olive-900 sm:grid-cols-[1fr_auto_auto] sm:items-center">
                  <strong>{order.id}</strong>
                  <span>{formatMoney(order.total)}</span>
                  <StatusBadge status={order.status} />
                </div>
              ))}
            </div>
          </div>
          <div className="rounded border border-cream/15 bg-white/8 p-4">
            <h3 className="font-bold">Prodotti piu vendibili</h3>
            <div className="mt-4 space-y-3">
              {products.slice(0, 5).map((product) => (
                <div key={product.id} className="flex items-center gap-3 rounded bg-cream p-3 text-olive-900">
                  <PackageOpen size={18} />
                  <span className="flex-1 text-sm font-semibold">{product.name}</span>
                  <strong>{formatMoney(product.price)}</strong>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded bg-gold p-4 text-olive-900">
              <p className="text-sm font-semibold">Ricavi mock</p>
              <p className="text-3xl font-bold">{formatMoney(revenue)}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
