import { PackageCheck } from "lucide-react";
import type { Order } from "../types";
import { StatusBadge } from "./StatusBadge";

export function TrackingCard({ order }: { order?: Order }) {
  return (
    <section id="tracking" className="bg-white py-12">
      <div className="mx-auto max-w-7xl px-4">
        <p className="text-sm font-semibold uppercase tracking-widest text-gold">Tracking package</p>
        <h2 className="mt-2 font-display text-4xl text-olive-900">Stato spedizione</h2>
        <div className="mt-6 rounded border border-olive-100 bg-cream p-5">
          {order?.trackingCode ? (
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <span className="grid h-14 w-14 place-items-center rounded bg-olive-900 text-cream">
                  <PackageCheck size={24} />
                </span>
                <div>
                  <h3 className="text-xl font-bold text-olive-900">{order.id}</h3>
                  <p className="text-olive-700">{order.carrier} · {order.trackingCode}</p>
                </div>
              </div>
              <StatusBadge status={order.status} />
            </div>
          ) : (
            <p className="text-olive-700">Quando un ordine viene spedito, qui appariranno corriere, codice e link tracking.</p>
          )}
        </div>
      </div>
    </section>
  );
}
