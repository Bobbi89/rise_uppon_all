import { CheckCircle2 } from "lucide-react";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

type Props = {
  order: { id: string; total: number; paid: boolean } | null;
  onClose: () => void;
};

export function SuccessSheet({ order, onClose }: Props) {
  return (
    <Sheet open={order !== null} title="Ordine confermato" onClose={onClose}>
      {order && (
        <div className="px-5 pb-6 text-center">
          <CheckCircle2 size={56} className="mx-auto text-olive-500" strokeWidth={1.5} />
          <h3 className="mt-3 font-display text-2xl font-semibold text-olive-900">Grazie!</h3>
          <p className="mt-2 text-sm leading-6 text-olive-700">
            Il tuo ordine <span className="font-extrabold text-olive-900">{order.id}</span> da{" "}
            <span className="font-extrabold text-olive-900">{formatMoney(order.total)}</span>{" "}
            {order.paid ? (
              <>è stato <b>pagato</b> con successo. Lo trovi in “I miei ordini” con lo stato e il tracking.</>
            ) : (
              <>è stato registrato. Ti contatteremo per completare il pagamento.</>
            )}
          </p>
          <div className="safe-bottom mt-6">
            <button
              className="w-full rounded-full bg-olive-900 py-3.5 text-sm font-extrabold text-cream active:scale-[0.98]"
              onClick={onClose}
            >
              Continua lo shopping
            </button>
          </div>
        </div>
      )}
    </Sheet>
  );
}
