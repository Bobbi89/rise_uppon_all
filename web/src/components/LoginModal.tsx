import { Mail, X } from "lucide-react";

type Props = {
  open: boolean;
  onClose: () => void;
  onGuest: () => void;
};

export function LoginModal({ open, onClose, onGuest }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-olive-900/45 p-4">
      <div className="w-full max-w-md rounded border border-olive-100 bg-white p-5 shadow-panel">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-2xl text-olive-900">Login utente</h2>
          <button className="rounded border border-olive-200 p-2" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <button className="mt-5 w-full rounded border border-olive-200 px-4 py-3 font-bold text-olive-900">
          Continua con Google
        </button>
        <div className="mt-4 grid gap-3">
          <input className="rounded border border-olive-200 px-4 py-3" placeholder="Email" />
          <input className="rounded border border-olive-200 px-4 py-3" placeholder="Password" type="password" />
          <button className="inline-flex items-center justify-center gap-2 rounded bg-olive-900 px-4 py-3 font-bold text-cream">
            <Mail size={17} />
            Entra con email
          </button>
          <button className="rounded px-4 py-3 font-bold text-clay" onClick={onGuest}>
            Continua come guest
          </button>
        </div>
      </div>
    </div>
  );
}
