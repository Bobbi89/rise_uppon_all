import { Boxes, ClipboardList, LockKeyhole, Menu, PackageSearch, ShoppingBag, ShoppingCart, UserRound } from "lucide-react";

type Props = {
  cartCount: number;
  onNavigate: (target: string) => void;
  onOpenLogin: () => void;
};

const navItems = [
  { label: "Catalogo", target: "catalog", icon: Boxes },
  { label: "Carrello", target: "cart", icon: ShoppingCart },
  { label: "Ordini", target: "orders", icon: ClipboardList },
  { label: "Tracking", target: "tracking", icon: PackageSearch },
  { label: "Admin", target: "admin", icon: LockKeyhole },
];

export function Navbar({ cartCount, onNavigate, onOpenLogin }: Props) {
  return (
    <header className="sticky top-0 z-40 border-b border-olive-100 bg-cream/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <button className="flex items-center gap-3 text-left" onClick={() => onNavigate("home")}>
          <span className="grid h-10 w-10 place-items-center rounded bg-olive-900 text-sm font-bold text-cream">ON</span>
          <span>
            <span className="block font-display text-xl text-olive-900">Oro Naturale</span>
            <span className="block text-xs uppercase tracking-widest text-olive-700">Telegram Shop</span>
          </span>
        </button>
        <nav className="hidden items-center gap-1 md:flex">
          {navItems.map(({ label, target, icon: Icon }) => (
            <button
              key={target}
              onClick={() => onNavigate(target)}
              className="inline-flex items-center gap-2 rounded px-3 py-2 text-sm font-semibold text-olive-900 hover:bg-olive-100"
            >
              <Icon size={17} />
              {label}
              {target === "cart" && cartCount > 0 ? (
                <span className="rounded-full bg-clay px-2 py-0.5 text-xs text-white">{cartCount}</span>
              ) : null}
            </button>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <button
            className="hidden items-center gap-2 rounded border border-olive-200 px-3 py-2 text-sm font-semibold text-olive-900 sm:inline-flex"
            onClick={onOpenLogin}
          >
            <UserRound size={17} />
            Login
          </button>
          <button
            className="inline-flex items-center gap-2 rounded bg-olive-900 px-3 py-2 text-sm font-semibold text-cream md:hidden"
            onClick={() => onNavigate("cart")}
          >
            <ShoppingBag size={17} />
            {cartCount}
          </button>
          <button className="rounded border border-olive-200 p-2 text-olive-900 md:hidden" onClick={() => onNavigate("catalog")}>
            <Menu size={18} />
          </button>
        </div>
      </div>
    </header>
  );
}
