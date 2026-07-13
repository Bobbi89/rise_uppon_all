import { Globe, Leaf, Search, ShieldCheck, ShoppingBag, User } from "lucide-react";
import { LANGS, useI18n } from "../i18n";

type Props = {
  cartCount: number;
  query: string;
  isAdmin: boolean;
  onQuery: (value: string) => void;
  onOpenCart: () => void;
  onOpenProfile: () => void;
  onOpenAdmin: () => void;
  onOpenLang: () => void;
};

export function Header({
  cartCount,
  query,
  isAdmin,
  onQuery,
  onOpenCart,
  onOpenProfile,
  onOpenAdmin,
  onOpenLang,
}: Props) {
  const { lang, t } = useI18n();
  const flag = LANGS.find((l) => l.code === lang)?.flag ?? "🌐";
  return (
    <header className="sticky top-0 z-40 bg-olive-900 px-4 pb-3 pt-4 text-cream">
      <div className="mx-auto flex max-w-lg items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-gold/20 text-gold-light">
            <Leaf size={18} />
          </span>
          <div className="leading-tight">
            <p className="font-display text-lg font-semibold tracking-wide">Oro Naturale</p>
            <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-gold-light">
              {t("tagline")}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            aria-label={t("changeLang")}
            className="flex h-10 items-center gap-1 rounded-full bg-olive-800 px-2.5 text-cream"
            onClick={onOpenLang}
          >
            <Globe size={15} className="text-olive-200" />
            <span className="text-sm leading-none">{flag}</span>
          </button>
          {isAdmin && (
            <button
              aria-label={t("adminPanel")}
              className="grid h-10 w-10 place-items-center rounded-full bg-olive-800 text-gold-light"
              onClick={onOpenAdmin}
            >
              <ShieldCheck size={18} />
            </button>
          )}
          <button
            aria-label={t("myOrdersAria")}
            className="grid h-10 w-10 place-items-center rounded-full bg-olive-800 text-cream"
            onClick={onOpenProfile}
          >
            <User size={18} />
          </button>
          <button
            aria-label={t("openCart")}
            className="relative grid h-10 w-10 place-items-center rounded-full bg-olive-800 text-cream"
            onClick={onOpenCart}
          >
            <ShoppingBag size={18} />
            {cartCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 grid min-w-[18px] place-items-center rounded-full bg-gold px-1 text-[10px] font-extrabold text-olive-900">
                {cartCount}
              </span>
            )}
          </button>
        </div>
      </div>
      <div className="mx-auto mt-3 flex max-w-lg items-center gap-2 rounded-xl bg-olive-800 px-3.5 py-2.5">
        <Search size={16} className="shrink-0 text-olive-200" />
        <input
          value={query}
          onChange={(event) => onQuery(event.target.value)}
          placeholder={t("search")}
          className="w-full bg-transparent text-sm text-cream placeholder:text-olive-200/70 focus:outline-none"
        />
      </div>
    </header>
  );
}
