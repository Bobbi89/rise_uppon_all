import { useState } from "react";
import { Leaf } from "lucide-react";
import type { Lang } from "../types";
import { LANGS } from "../i18n";

type Props = {
  initial: Lang;
  onConfirm: (lang: Lang) => void;
};

// Bilingue statico: mostrato prima di conoscere la lingua scelta.
const TITLE: Record<Lang, string> = {
  it: "Scegli la lingua",
  en: "Choose your language",
  ro: "Alege limba",
  es: "Elige el idioma",
  no: "Velg språk",
};
const SUBTITLE: Record<Lang, string> = {
  it: "Benvenuto in Oro Naturale",
  en: "Welcome to Oro Naturale",
  ro: "Bine ai venit la Oro Naturale",
  es: "Bienvenido a Oro Naturale",
  no: "Velkommen til Oro Naturale",
};
const CONTINUE: Record<Lang, string> = {
  it: "Continua",
  en: "Continue",
  ro: "Continuă",
  es: "Continuar",
  no: "Fortsett",
};

/** Schermata iniziale di scelta lingua (EN / IT / RO / ES). */
export function LanguageGate({ initial, onConfirm }: Props) {
  const [sel, setSel] = useState<Lang>(initial);

  return (
    <div className="fixed inset-0 z-[60] flex flex-col items-center justify-center bg-olive-900 px-6 text-cream">
      <div className="w-full max-w-sm text-center">
        <span className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-gold/20 text-gold-light">
          <Leaf size={30} />
        </span>
        <p className="mt-4 font-display text-2xl font-semibold tracking-wide">Oro Naturale</p>
        <p className="mt-1 text-[13px] text-gold-light">{SUBTITLE[sel]}</p>

        <h1 className="mt-8 text-[12px] font-bold uppercase tracking-[0.2em] text-olive-200">
          {TITLE[sel]}
        </h1>

        <div className="mt-4 grid grid-cols-2 gap-3">
          {LANGS.map((l) => (
            <button
              key={l.code}
              onClick={() => setSel(l.code)}
              className={`flex items-center gap-3 rounded-2xl border px-4 py-4 text-left transition-colors ${
                sel === l.code
                  ? "border-gold bg-olive-800"
                  : "border-olive-700 bg-olive-800/40"
              }`}
            >
              <span className="text-2xl">{l.flag}</span>
              <span className="text-sm font-bold">{l.label}</span>
            </button>
          ))}
        </div>

        <button
          onClick={() => onConfirm(sel)}
          className="mt-8 w-full rounded-full bg-gold py-3.5 text-sm font-extrabold text-olive-900 active:scale-[0.98]"
        >
          {CONTINUE[sel]}
        </button>
      </div>
    </div>
  );
}
