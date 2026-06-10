import type { OrderStatus } from "../types";

const statusClass: Record<OrderStatus, string> = {
  "da pagare": "border-amber-300 bg-amber-50 text-amber-800",
  pagato: "border-emerald-300 bg-emerald-50 text-emerald-800",
  "in preparazione": "border-sky-300 bg-sky-50 text-sky-800",
  spedito: "border-indigo-300 bg-indigo-50 text-indigo-800",
  consegnato: "border-olive-300 bg-olive-50 text-olive-800",
};

export function StatusBadge({ status }: { status: OrderStatus }) {
  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${statusClass[status]}`}>
      {status}
    </span>
  );
}
