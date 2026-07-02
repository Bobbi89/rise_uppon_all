import type { ReactNode } from "react";
import { X } from "lucide-react";

type Props = {
  open: boolean;
  title?: string;
  onClose: () => void;
  children: ReactNode;
};

/** Bottom sheet stile Telegram: backdrop scuro + pannello che sale dal basso. */
export function Sheet({ open, title, onClose, children }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <div className="absolute inset-0 animate-fade-in bg-olive-900/50" onClick={onClose} />
      <div className="relative z-10 flex max-h-[92dvh] w-full max-w-lg animate-slide-up flex-col overflow-hidden rounded-t-3xl bg-cream shadow-sheet">
        <div className="mx-auto mt-2.5 h-1 w-10 shrink-0 rounded-full bg-olive-200" />
        <div className="flex shrink-0 items-center justify-between px-5 pb-2 pt-3">
          <h2 className="font-display text-lg font-semibold text-olive-900">{title}</h2>
          <button
            aria-label="Chiudi"
            className="grid h-8 w-8 place-items-center rounded-full bg-olive-100 text-olive-700"
            onClick={onClose}
          >
            <X size={16} strokeWidth={2.5} />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
