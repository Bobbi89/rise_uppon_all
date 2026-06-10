export type CategoryId =
  | "extra_virgin_olive_oil"
  | "flavored_oil"
  | "wine"
  | "cosmetics"
  | "gift_box"
  | "gourmet";

export type Product = {
  id: string;
  name: string;
  category: CategoryId;
  price: number;
  image: string;
  description: string;
  volume?: string;
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

export type PaymentMethod = "stripe" | "revolut";

export type ShippingDetails = {
  name: string;
  email: string;
  address: string;
  city: string;
  country: string;
};
