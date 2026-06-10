import { useMemo, useState } from "react";
import { AdminDashboard } from "./components/AdminDashboard";
import { CartSidebar } from "./components/CartSidebar";
import { CategoryTabs } from "./components/CategoryTabs";
import { CheckoutForm } from "./components/CheckoutForm";
import { Hero } from "./components/Hero";
import { LoginModal } from "./components/LoginModal";
import { Navbar } from "./components/Navbar";
import { OrdersList } from "./components/OrdersList";
import { ProductCard } from "./components/ProductCard";
import { ProductDrawer } from "./components/ProductDrawer";
import { TrackingCard } from "./components/TrackingCard";
import { categories, initialOrders, products } from "./data/mockData";
import type { CartItem, CategoryId, Order, PaymentMethod, Product, ShippingDetails } from "./types";
import { formatMoney } from "./utils/money";

const freeShippingMin = 100;
const defaultShipping = 14;

function scrollToSection(id: string) {
  const node = document.getElementById(id);
  if (node) node.scrollIntoView({ behavior: "smooth", block: "start" });
}

export default function App() {
  const [activeCategory, setActiveCategory] = useState<CategoryId>("extra_virgin_olive_oil");
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [orders, setOrders] = useState<Order[]>(initialOrders);
  const [cartOpen, setCartOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const [lastPayment, setLastPayment] = useState<PaymentMethod | null>(null);

  const filteredProducts = products.filter((product) => product.category === activeCategory);
  const subtotal = cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  const shipping = cart.length === 0 || subtotal >= freeShippingMin ? 0 : defaultShipping;
  const total = subtotal + shipping;
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const featuredOrder = orders.find((order) => order.trackingCode);

  const relatedProducts = useMemo(() => {
    if (!selectedProduct) return [];
    return products.filter((product) => product.category === selectedProduct.category && product.id !== selectedProduct.id);
  }, [selectedProduct]);

  function addToCart(product: Product, quantity = 1) {
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
    setCartOpen(true);
  }

  function updateCart(productId: string, quantity: number) {
    if (quantity <= 0) {
      setCart((current) => current.filter((item) => item.product.id !== productId));
      return;
    }
    setCart((current) => current.map((item) => (item.product.id === productId ? { ...item, quantity } : item)));
  }

  function navigate(target: string) {
    if (target === "cart") {
      setCartOpen(true);
      return;
    }
    scrollToSection(target);
  }

  function confirmOrder(details: ShippingDetails, method: PaymentMethod) {
    const order: Order = {
      id: `ON-${Math.floor(10000 + Math.random() * 89999)}`,
      date: new Date().toISOString().slice(0, 10),
      status: "pagato",
      total,
      items: cart,
    };
    setOrders((current) => [order, ...current]);
    setCart([]);
    setLastPayment(method);
    alert(`Ordine ${order.id} generato per ${details.name}. Metodo: ${method === "stripe" ? "Stripe" : "Revolut Pay"}.`);
    scrollToSection("orders");
  }

  return (
    <div className="min-h-screen bg-cream font-body text-olive-900">
      <Navbar cartCount={cartCount} onNavigate={navigate} onOpenLogin={() => setLoginOpen(true)} />
      <main>
        <div id="home">
          <Hero onCatalog={() => scrollToSection("catalog")} onCart={() => setCartOpen(true)} />
        </div>

        <section id="catalog" className="bg-cream py-12">
          <div className="mx-auto max-w-7xl px-4">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-widest text-gold">Catalogo prodotti</p>
                <h2 className="mt-2 font-display text-4xl text-olive-900">Scegli, aggiungi, paga</h2>
              </div>
              <div className="rounded border border-olive-100 bg-white px-4 py-3 text-sm font-semibold text-olive-700">
                Spedizione gratis da {formatMoney(freeShippingMin)}
              </div>
            </div>
            <div className="mt-6">
              <CategoryTabs active={activeCategory} onChange={setActiveCategory} />
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} onAdd={addToCart} onView={setSelectedProduct} />
              ))}
            </div>
          </div>
        </section>

        <CheckoutForm items={cart} total={total} onConfirm={confirmOrder} />
        <OrdersList orders={orders} />
        <TrackingCard order={featuredOrder} />
        <AdminDashboard orders={orders} products={products} />
      </main>

      <footer className="bg-cream px-4 py-8 text-center text-sm text-olive-700">
        Oro Naturale SRL · biomarketshop.com · Stripe/Revolut Pay ready
        {lastPayment ? <span className="block mt-2">Ultimo metodo selezionato: {lastPayment}</span> : null}
      </footer>

      <ProductDrawer
        product={selectedProduct}
        related={relatedProducts}
        onClose={() => setSelectedProduct(null)}
        onAdd={addToCart}
        onView={setSelectedProduct}
      />
      <CartSidebar
        open={cartOpen}
        items={cart}
        subtotal={subtotal}
        shipping={shipping}
        total={total}
        onClose={() => setCartOpen(false)}
        onUpdate={updateCart}
        onRemove={(productId) => setCart((current) => current.filter((item) => item.product.id !== productId))}
        onClear={() => setCart([])}
        onCheckout={() => {
          setCartOpen(false);
          scrollToSection("checkout");
        }}
      />
      <LoginModal open={loginOpen} onClose={() => setLoginOpen(false)} onGuest={() => setLoginOpen(false)} />
    </div>
  );
}
