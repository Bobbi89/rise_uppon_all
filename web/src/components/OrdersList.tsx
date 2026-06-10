import type { Order } from "../types";
import { formatMoney } from "../utils/money";
import { StatusBadge } from "./StatusBadge";

export function OrdersList({ orders }: { orders: Order[] }) {
  return (
    <section id="orders" className="bg-cream py-12">
      <div className="mx-auto max-w-7xl px-4">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-gold">Area utente</p>
            <h2 className="mt-2 font-display text-4xl text-olive-900">I miei ordini</h2>
          </div>
          <span className="text-sm font-semibold text-olive-700">{orders.length} ordini salvati</span>
        </div>
        <div className="mt-6 grid gap-4">
          {orders.map((order) => (
            <article key={order.id} className="rounded border border-olive-100 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-xl font-bold text-olive-900">{order.id}</h3>
                  <p className="text-sm text-olive-700">{order.date} · {formatMoney(order.total)}</p>
                </div>
                <StatusBadge status={order.status} />
              </div>
              <div className="mt-4 grid gap-2 text-sm text-olive-700">
                {order.items.map((item) => (
                  <div key={item.product.id} className="flex justify-between">
                    <span>{item.product.name} x{item.quantity}</span>
                    <strong>{formatMoney(item.product.price * item.quantity)}</strong>
                  </div>
                ))}
              </div>
              {order.trackingCode ? (
                <a className="mt-4 inline-block font-bold text-clay" href={order.trackingUrl} target="_blank" rel="noreferrer">
                  Tracking {order.carrier}: {order.trackingCode}
                </a>
              ) : null}
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
