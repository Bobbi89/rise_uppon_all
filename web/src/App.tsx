import { useEffect, useMemo, useState } from "react";
import { CartSheet } from "./components/CartSheet";
import { CategoryChips } from "./components/CategoryChips";
import { CheckoutSheet } from "./components/CheckoutSheet";
import { Header } from "./components/Header";
import { ProductCard } from "./components/ProductCard";
import { ProductSheet } from "./components/ProductSheet";
import { SuccessSheet } from "./components/SuccessSheet";
import { products } from "./data/products";
import { getTelegram, haptic, hapticSuccess, initTelegram, telegramUserName } from "./telegram";
import type { CartItem, CategoryFilter, Order, PaymentMethod, Product, ShippingDetails } from "./types";
import { formatMoney } from "./utils/money";

const FREE_SHIPPING_MIN = 100;
const DEFAULT_SHIPPING = 14;

export default function App() {
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [cartOpen, setCartOpen] = useState(false);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [confirmedOrder, setConfirmedOrder] = useState<Order | null>(null);

  useEffect(() => {
    initTelegram();
  }, []);

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
  const shipping = cart.length === 0 || subtotal >= FREE_SHIPPING_MIN ? 0 : DEFAULT_SHIPPING;
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

  function confirmOrder(details: ShippingDetails, method: PaymentMethod) {
    const order: Order = {
      id: `ON-${Math.floor(10000 + Math.random() * 89999)}`,
      date: new Date().toISOString().slice(0, 10),
      status: "da pagare",
      total,
      items: cart,
    };

    hapticSuccess();
    setCheckoutOpen(false);
    setCart([]);

    // Se la mini app è stata aperta dal pulsante keyboard del bot,
    // l'ordine arriva al bot via web_app_data e Telegram chiude la webapp.
    const tg = getTelegram();
    if (tg) {
      try {
        tg.sendData(
          JSON.stringify({
            type: "order",
            order_id: order.id,
            total,
            shipping,
            payment_method: method,
            customer: details,
            items: cart.map((item) => ({
              id: item.product.id,
              name: item.product.name,
              price: item.product.price,
              quantity: item.quantity,
            })),
          }),
        );
      } catch {
        // aperta come link diretto: sendData non disponibile
      }
    }
    setConfirmedOrder(order);
  }

  const overlayOpen = selectedProduct !== null || cartOpen || checkoutOpen || confirmedOrder !== null;

  return (
    <div className="mx-auto min-h-dvh max-w-lg bg-cream font-body text-olive-900">
      <Header
        cartCount={cartCount}
        query={query}
        onQuery={setQuery}
        onOpenCart={() => setCartOpen(true)}
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
          {filteredProducts.length} prodotti · Spedizione gratis da {formatMoney(FREE_SHIPPING_MIN)}
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
            {filteredProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAdd={(item) => addToCart(item, 1)}
                onView={setSelectedProduct}
              />
            ))}
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
        freeShippingMin={FREE_SHIPPING_MIN}
        onClose={() => setCartOpen(false)}
        onUpdate={updateCart}
        onCheckout={() => {
          setCartOpen(false);
          setCheckoutOpen(true);
        }}
      />

      <CheckoutSheet
        open={checkoutOpen}
        items={cart}
        total={total}
        defaultName={telegramUserName() ?? undefined}
        onClose={() => setCheckoutOpen(false)}
        onConfirm={confirmOrder}
      />

      <SuccessSheet order={confirmedOrder} onClose={() => setConfirmedOrder(null)} />
    </div>
  );
}
