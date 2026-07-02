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

export type PaymentMethod = "stripe" | "revolut" | "bonifico";

export type ShippingDetails = {
  name: string;
  phone: string;
  address: string;
  city: string;
  zip: string;
  notes?: string;
};
