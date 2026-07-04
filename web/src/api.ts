// Client dell'API della Mini App (same-origin /api, servita dal bot su Railway).
import { telegramInitData } from "./telegram";
import type { PaymentMethod, ServerOrder, ShippingDetails } from "./types";

export type ApiConfig = {
  revolut_public_key: string;
  revolut_mode: "sandbox" | "prod";
  revolut_enabled: boolean;
  currency: string;
  free_shipping_min: number;
  default_shipping: number;
  is_admin: boolean;
};

export type CreateOrderResult = {
  order_id: string;
  total: number;
  subtotal: number;
  shipping: number;
  currency: string;
  revolut_token: string | null;
  revolut_public_key: string;
  revolut_mode: "sandbox" | "prod";
};

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Init-Data": telegramInitData(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.error || body.detail || message;
    } catch {
      /* corpo non JSON */
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getConfig: () => apiFetch<ApiConfig>("/config"),

  createOrder: (items: { id: string; quantity: number }[], shipping: ShippingDetails) =>
    apiFetch<CreateOrderResult>("/orders", {
      method: "POST",
      body: JSON.stringify({ items, shipping }),
    }),

  confirmOrder: (orderId: string, paymentMethod: PaymentMethod) =>
    apiFetch<{ order: ServerOrder; paid: boolean }>(`/orders/${orderId}/confirm`, {
      method: "POST",
      body: JSON.stringify({ payment_method: paymentMethod }),
    }),

  getProfile: () =>
    apiFetch<{ customer: Record<string, unknown> | null; orders: ServerOrder[] }>("/profile"),

  adminOrders: () => apiFetch<{ orders: ServerOrder[] }>("/admin/orders"),

  setTracking: (orderId: string, data: { carrier: string; code: string; url?: string }) =>
    apiFetch<{ order: ServerOrder }>(`/admin/orders/${orderId}/tracking`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
