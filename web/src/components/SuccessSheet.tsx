import { CheckCircle2, Clock, Copy } from "lucide-react";
import { formatMoney } from "../utils/money";
import { Sheet } from "./Sheet";

type Props = {
  order: {
    id: string;
    total: number;
    paid: boolean;
    paypalEmail?: string;
    paypalLink?: string | null;
  } | null;
  onClose: () => void;
};

export function SuccessSheet({ order, onClose }: Props) {
  const isPaypal = !!(order && !order.paid && order.paypalEmail);

  function copyEmail() {
    if (order?.paypalEmail) {
      navigator.clipboard?.writeText(order.paypalEmail).catch(() => {});
    }
  }

  return (
    <Sheet open={order !== null} title={isPaypal ? "Ordine registrato" : "Ordine confermato"} onClose={onClose}>
      {order && (
        <div className="px-5 pb-6 text-center">
          {isPaypal ? (
            <Clock size={56} className="mx-auto text-gold" strokeWidth={1.5} />
          ) : (
            <CheckCircle2 size={56} className="mx-auto text-olive-500" strokeWidth={1.5} />
          )}
          <h3 className="mt-3 font-display text-2xl font-semibold text-olive-900">Grazie!</h3>
          <p className="mt-2 text-sm leading-6 text-olive-700">
            Il tuo ordine <span className="font-extrabold text-olive-900">{order.id}</span> da{" "}
            <span className="font-extrabold text-olive-900">{formatMoney(order.total)}</span>{" "}
            {order.paid ? (
              <>è stato <b>pagato</b> con successo. Lo trovi in “I miei ordini” con lo stato e il tracking.</>
            ) : isPaypal ? (
              <>è stato registrato. Completa il pagamento su PayPal per confermarlo.</>
            ) : (
              <>è stato registrato. Ti contatteremo per completare il pagamento.</>
            )}
          </p>

          {isPaypal && (
            <div className="mt-4 rounded-2xl border border-olive-100 bg-white p-4 text-left">
              <p className="text-[11px] font-bold uppercase tracking-widest text-gold">Pagamento PayPal</p>
              <p className="mt-2 text-[13px] leading-5 text-olive-700">
                Invia <b>{formatMoney(order.total)}</b> a questo account PayPal:
              </p>
              <button
                onClick={copyEmail}
                className="mt-2 flex w-full items-center justify-between gap-2 rounded-xl border border-olive-100 bg-cream px-3 py-2.5 text-left text-[13px] font-bold text-olive-900 active:scale-[0.99]"
              >
                <span className="truncate">{order.paypalEmail}</span>
                <Copy size={16} className="shrink-0 text-olive-500" />
              </button>
              {order.paypalLink && (
                <a
                  href={order.paypalLink}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 block w-full rounded-xl bg-[#0070ba] py-2.5 text-center text-[13px] font-extrabold text-white active:scale-[0.99]"
                >
                  Paga con PayPal.me
                </a>
              )}
              <p className="mt-3 text-[11px] leading-4 text-olive-400">
                Indica il numero d'ordine <b>{order.id}</b> nella causale. Confermeremo la spedizione
                appena ricevuto il pagamento.
              </p>
            </div>
          )}

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
