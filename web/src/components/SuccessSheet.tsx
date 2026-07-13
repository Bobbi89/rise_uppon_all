import { CheckCircle2, Clock, Copy } from "lucide-react";
import { useI18n } from "../i18n";
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
  const { t } = useI18n();
  const isPaypal = !!(order && !order.paid && order.paypalEmail);

  function copyEmail() {
    if (order?.paypalEmail) {
      navigator.clipboard?.writeText(order.paypalEmail).catch(() => {});
    }
  }

  return (
    <Sheet open={order !== null} title={isPaypal ? t("orderRegistered") : t("orderConfirmed")} onClose={onClose}>
      {order && (
        <div className="px-5 pb-6 text-center">
          {isPaypal ? (
            <Clock size={56} className="mx-auto text-gold" strokeWidth={1.5} />
          ) : (
            <CheckCircle2 size={56} className="mx-auto text-olive-500" strokeWidth={1.5} />
          )}
          <h3 className="mt-3 font-display text-2xl font-semibold text-olive-900">{t("thanks")}</h3>
          <p className="mt-2 text-sm leading-6 text-olive-700">
            {t("yourOrder")} <span className="font-extrabold text-olive-900">{order.id}</span> {t("ofAmount")}{" "}
            <span className="font-extrabold text-olive-900">{formatMoney(order.total)}</span>{" "}
            {order.paid ? t("successPaid") : isPaypal ? t("successPaypal") : t("successPending")}
          </p>

          {isPaypal && (
            <div className="mt-4 rounded-2xl border border-olive-100 bg-white p-4 text-left">
              <p className="text-[11px] font-bold uppercase tracking-widest text-gold">{t("paypalPayment")}</p>
              <p className="mt-2 text-[13px] leading-5 text-olive-700">
                {t("paypalSendTo", { amount: formatMoney(order.total) })}
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
                  {t("payWithPaypalMe")}
                </a>
              )}
              <p className="mt-3 text-[11px] leading-4 text-olive-400">
                {t("paypalReference", { id: order.id })}
              </p>
            </div>
          )}

          <div className="safe-bottom mt-6">
            <button
              className="w-full rounded-full bg-olive-900 py-3.5 text-sm font-extrabold text-cream active:scale-[0.98]"
              onClick={onClose}
            >
              {t("continueShopping")}
            </button>
          </div>
        </div>
      )}
    </Sheet>
  );
}
