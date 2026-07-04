export type CategoryId =
  | "extra_virgin_olive_oil"
  | "flavored_oils"
  | "wines"
  | "cosmetics"
  | "gift_boxes";

export type CategoryFilter = CategoryId | "all";

export type Category = {
  id: CategoryFilter;
  label: string;
  emoji: string;
};

export type Product = {
  id: string;
  name: string;
  category: CategoryId;
  price: number;
  image: string;
  description: string;
  volume?: string;
  origin?: string;
  tags?: string[];
  featured?: boolean;
  stock: number;
};

export type CartItem = {
  product: Product;
  quantity: number;
};

export type OrderStatus = "da pagare" | "pagato" | "in preparazione" | "spedito" | "consegnato";

export type Order = {
  id: string;
  date: string;
  status: OrderStatus;
  total: number;
  items: CartItem[];
  carrier?: string;
  trackingCode?: string;
  trackingUrl?: string;
};

export type PaymentMethod = "revolut" | "revolut_pay" | "apple_pay" | "card";

export type ShippingDetails = {
  name: string;
  phone: string;
  address: string;
  city: string;
  zip: string;
  notes?: string;
};

/** Ordine come restituito dall'API/DB (profilo utente e admin). */
export type ServerOrder = {
  id: string;
  user_id?: number;
  username?: string;
  items: { id: string; name: string; price: number; quantity: number }[];
  subtotal: number;
  shipping: number;
  total: number;
  currency: string;
  status: string;
  payment_method?: string | null;
  shipping_name?: string | null;
  shipping_phone?: string | null;
  shipping_address?: string | null;
  shipping_city?: string | null;
  shipping_zip?: string | null;
  shipping_notes?: string | null;
  tracking_carrier?: string | null;
  tracking_code?: string | null;
  tracking_url?: string | null;
  tracking_status?: string | null;
  created_at?: string;
  paid_at?: string | null;
};
