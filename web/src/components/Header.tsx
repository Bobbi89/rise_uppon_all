import { Leaf, Search, ShoppingBag } from "lucide-react";

type Props = {
  cartCount: number;
  query: string;
  onQuery: (value: string) => void;
  onOpenCart: () => void;
};

export function Header({ cartCount, query, onQuery, onOpenCart }: Props) {
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
              Bio Marketplace
            </p>
          </div>
        </div>
        <button
          aria-label="Apri carrello"
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
      <div className="mx-auto mt-3 flex max-w-lg items-center gap-2 rounded-xl bg-olive-800 px-3.5 py-2.5">
        <Search size={16} className="shrink-0 text-olive-200" />
        <input
          value={query}
          onChange={(event) => onQuery(event.target.value)}
          placeholder="Cerca olio, vino, cosmetica…"
          className="w-full bg-transparent text-sm text-cream placeholder:text-olive-200/70 focus:outline-none"
        />
      </div>
    </header>
  );
}
