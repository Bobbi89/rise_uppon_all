import { useEffect, useMemo, useState } from "react";
import { api, type ApiConfig } from "./api";
import { AdminSheet } from "./components/AdminSheet";
import { CartSheet } from "./components/CartSheet";
import { CategoryChips } from "./components/CategoryChips";
import { CheckoutSheet, type PayChoice } from "./components/CheckoutSheet";
import { Header } from "./components/Header";
import { ProductCard } from "./components/ProductCard";
import { ProductSheet } from "./components/ProductSheet";
import { ProfileSheet } from "./components/ProfileSheet";
import { SuccessSheet } from "./components/SuccessSheet";
import { products } from "./data/products";
import { payWithRevolut } from "./revolut";
import { haptic, hapticError, hapticSuccess, initTelegram, telegramUserName } from "./telegram";
import type { CartItem, CategoryFilter, Product, ShippingDetails } from "./types";
import { formatMoney } from "./utils/money";

const DEFAULTS = { free_shipping_min: 100, default_shipping: 14 };

export default function App() {
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [cartOpen, setCartOpen] = useState(false);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const [confirmedOrder, setConfirmedOrder] = useState<{
    id: string;
    total: number;
    paid: boolean;
    paypalEmail?: string;
    paypalLink?: string | null;
  } | null>(null);

  const [config, setConfig] = useState<ApiConfig | null>(null);
  const [processing, setProcessing] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);

  useEffect(() => {
    initTelegram();
    api.getConfig().then(setConfig).catch(() => setConfig(null));
  }, []);

  const freeShippingMin = config?.free_shipping_min ?? DEFAULTS.free_shipping_min;
  const defaultShipping = config?.default_shipping ?? DEFAULTS.default_shipping;

  const filteredProducts = useMemo(() => {
    const term = query.trim().toLowerCase();
    return products.filter((product) => {
      if (category !== "all" && product.category !== category) return false;
      if (!term) return true;
      return (
        product.name.toLowerCase().includes(term) ||
        product.description.toLowerCase().includes(term)
      );
    });
  }, [category, query]);

  const subtotal = cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  const shipping = cart.length === 0 || subtotal >= freeShippingMin ? 0 : defaultShipping;
  const total = subtotal + shipping;
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  function addToCart(product: Product, quantity = 1) {
    haptic("light");
    setCart((current) => {
      const existing = current.find((item) => item.product.id === product.id);
      if (existing) {
        return current.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + quantity } : item,
        );
      }
      return [...current, { product, quantity }];
    });
    setSelectedProduct(null);
  }

  function updateCart(productId: string, quantity: number) {
    haptic("light");
    if (quantity <= 0) {
      setCart((current) => current.filter((item) => item.product.id !== productId));
      return;
    }
    setCart((current) =>
      current.map((item) => (item.product.id === productId ? { ...item, quantity } : item)),
    );
  }

  // Flusso pagamento: crea ordine (server) → Revolut (carta) o PayPal (istruzioni).
  async function pay(details: ShippingDetails, method: PayChoice) {
    if (processing) return;
    setProcessing(true);
    setCheckoutError(null);
    try {
      const items = cart.map((item) => ({ id: item.product.id, quantity: item.quantity }));
      const created = await api.createOrder(items, details, method);

      if (method === "paypal") {
        // Ordine registrato "in attesa di pagamento": mostra le istruzioni PayPal.
        hapticSuccess();
        finishOrder(created.order_id, created.total, false, {
          paypalEmail: created.paypal_email,
          paypalLink: created.paypal_link,
        });
        return;
      }

      if (!created.revolut_token) {
        // Revolut non configurato: ordine registrato come "da pagare".
        hapticSuccess();
        finishOrder(created.order_id, created.total, false);
        return;
      }

      const outcome = await payWithRevolut(created.revolut_token, created.revolut_mode ?? "prod");
      if (outcome === "cancel") {
        setProcessing(false);
        return; // l'utente ha annullato: resta nel checkout
      }

      const confirmation = await api.confirmOrder(created.order_id, "revolut");
      if (confirmation.paid) {
        hapticSuccess();
        finishOrder(created.order_id, created.total, true);
      } else {
        hapticError();
        setCheckoutError("Pagamento non confermato. Riprova o contattaci.");
        setProcessing(false);
      }
    } catch (e) {
      hapticError();
      setCheckoutError((e as Error).message || "Errore durante il pagamento.");
      setProcessing(false);
    }
  }

  function finishOrder(
    id: string,
    orderTotal: number,
    paid: boolean,
    paypal?: { paypalEmail?: string; paypalLink?: string | null },
  ) {
    setProcessing(false);
    setCheckoutOpen(false);
    setCart([]);
    setConfirmedOrder({
      id,
      total: orderTotal,
      paid,
      paypalEmail: paypal?.paypalEmail,
      paypalLink: paypal?.paypalLink,
    });
  }

  const overlayOpen =
    selectedProduct !== null ||
    cartOpen ||
    checkoutOpen ||
    profileOpen ||
    adminOpen ||
    confirmedOrder !== null;

  return (
    <div className="mx-auto min-h-dvh max-w-lg bg-cream font-body text-olive-900">
      <Header
        cartCount={cartCount}
        query={query}
        isAdmin={config?.is_admin ?? false}
        onQuery={setQuery}
        onOpenCart={() => setCartOpen(true)}
        onOpenProfile={() => setProfileOpen(true)}
        onOpenAdmin={() => setAdminOpen(true)}
      />

      <main className="px-4 pb-28 pt-3">
        <CategoryChips
          active={category}
          onChange={(next) => {
            haptic("light");
            setCategory(next);
          }}
        />

        <p className="mt-2 text-[12px] font-semibold text-olive-400">
          {filteredProducts.length} prodotti · Spedizione gratis da {formatMoney(freeShippingMin)}
        </p>

        {filteredProducts.length === 0 ? (
          <div className="mt-14 text-center">
            <p className="text-4xl">🌿</p>
            <p className="mt-3 text-sm font-semibold text-olive-700">
              Nessun prodotto trovato. Prova un'altra ricerca.
            </p>
          </div>
        ) : (
          <div className="mt-3 grid grid-cols-2 gap-2.5 min-[480px]:grid-cols-3">
            {filteredProducts.map((product) => {
              const inCart = cart.find((item) => item.product.id === product.id)?.quantity ?? 0;
              return (
                <ProductCard
                  key={product.id}
                  product={product}
                  quantity={inCart}
                  onAdd={(item) => addToCart(item, 1)}
                  onDecrement={(item) => updateCart(item.id, inCart - 1)}
                  onView={setSelectedProduct}
                />
              );
            })}
          </div>
        )}

        <footer className="mt-10 pb-4 text-center text-[11px] leading-5 text-olive-400">
          Oro Naturale SRL · Prodotti biologici italiani
          <br />
          biomarketshop.com
        </footer>
      </main>

      {cartCount > 0 && !overlayOpen && (
        <div className="safe-bottom fixed inset-x-0 bottom-0 z-40 mx-auto max-w-lg px-4 pb-3">
          <button
            className="flex w-full items-center justify-between rounded-full bg-olive-900 px-5 py-3.5 text-sm font-extrabold text-cream shadow-bar active:scale-[0.98]"
            onClick={() => setCartOpen(true)}
          >
            <span>🛒 Carrello · {cartCount} {cartCount === 1 ? "articolo" : "articoli"}</span>
            <span>{formatMoney(total)}</span>
          </button>
        </div>
      )}

      <ProductSheet product={selectedProduct} onClose={() => setSelectedProduct(null)} onAdd={addToCart} />

      <CartSheet
        open={cartOpen}
        items={cart}
        subtotal={subtotal}
        shipping={shipping}
        total={total}
        freeShippingMin={freeShippingMin}
        onClose={() => setCartOpen(false)}
        onUpdate={updateCart}
        onCheckout={() => {
          setCartOpen(false);
          setCheckoutError(null);
          setCheckoutOpen(true);
        }}
      />

      <CheckoutSheet
        open={checkoutOpen}
        items={cart}
        total={total}
        defaultName={telegramUserName() ?? undefined}
        processing={processing}
        error={checkoutError}
        revolutEnabled={config?.revolut_enabled ?? false}
        paypalEnabled={config?.paypal_enabled ?? false}
        onClose={() => {
          if (!processing) setCheckoutOpen(false);
        }}
        onPay={pay}
      />

      <ProfileSheet open={profileOpen} onClose={() => setProfileOpen(false)} />
      <AdminSheet open={adminOpen} onClose={() => setAdminOpen(false)} />

      <SuccessSheet order={confirmedOrder} onClose={() => setConfirmedOrder(null)} />
    </div>
  );
}
