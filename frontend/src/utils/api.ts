import type {
  AdminChannelPost,
  AdminPaymentSettings,
  AdminPaymentTicket,
  AdminProduct,
  AdminProductPayload,
  AdminPromoCode,
  AdminPromoCodePayload,
  AdminPromotion,
  AdminStats,
  AdminUploadedImage,
  Cart,
  Category,
  CheckoutPaymentConfig,
  Favorite,
  Order,
  Product,
} from "types/api";
import { getRuntimeApiUrl } from "utils/runtime-config";
import { getAuthHeaders } from "utils/telegram";

const API_URL = getRuntimeApiUrl();

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...getAuthHeaders(),
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Ошибка запроса";
    const raw = await response.text();
    if (raw) {
      try {
        const payload = JSON.parse(raw) as { detail?: string };
        message = payload.detail || raw || message;
      } catch {
        message = raw;
      }
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getCategories: () => request<Category[]>("/categories"),
  getCategory: (slug: string) => request<Category>(`/categories/${slug}`),
  getProducts: (params?: URLSearchParams) =>
    request<Product[]>(`/products${params ? `?${params.toString()}` : ""}`),
  getFeaturedProducts: () => request<Product[]>("/products/featured"),
  searchProducts: (q: string) => request<Product[]>(`/products/search?q=${encodeURIComponent(q)}`),
  getProduct: (slug: string) => request<Product>(`/products/${slug}`),
  getFavorites: () => request<Favorite[]>("/favorites"),
  toggleFavorite: (productId: number) =>
    request<{ is_favorite: boolean }>("/favorites/toggle", {
      method: "POST",
      body: JSON.stringify({ product_id: productId }),
    }),
  getCart: (promoCode?: string) =>
    request<Cart>(`/cart${promoCode ? `?promo_code=${encodeURIComponent(promoCode)}` : ""}`),
  addToCart: (productId: number, packSizeId: number | null, qty = 1) =>
    request<{ message: string }>("/cart/add", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, pack_size_id: packSizeId, qty }),
    }),
  updateCart: (cartItemId: number, qty: number) =>
    request<{ message: string }>("/cart/update", {
      method: "POST",
      body: JSON.stringify({ cart_item_id: cartItemId, qty }),
    }),
  removeFromCart: (cartItemId: number) =>
    request<{ message: string }>("/cart/remove", {
      method: "POST",
      body: JSON.stringify({ cart_item_id: cartItemId }),
    }),
  createOrder: (payload: {
    customer_name: string;
    customer_phone: string;
    comment?: string;
    delivery_type: "pickup" | "city_delivery";
    promo_code?: string;
  }) =>
    request<Order>("/orders/create", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getOrder: (id: string) => request<Order>(`/orders/${id}`),
  getCheckoutPaymentConfig: () => request<CheckoutPaymentConfig>("/payment-tickets/checkout-config"),
  createPaymentTicket: (payload: {
    customer_name: string;
    customer_phone: string;
    customer_contact: string;
    comment?: string;
    delivery_type: "pickup" | "city_delivery";
    promo_code?: string;
    payment_screenshot: File;
  }) => {
    const formData = new FormData();
    formData.set("customer_name", payload.customer_name);
    formData.set("customer_phone", payload.customer_phone);
    formData.set("customer_contact", payload.customer_contact);
    formData.set("delivery_type", payload.delivery_type);
    formData.set("payment_screenshot", payload.payment_screenshot);
    if (payload.comment) formData.set("comment", payload.comment);
    if (payload.promo_code) formData.set("promo_code", payload.promo_code);

    return request<Order>("/payment-tickets/create", {
      method: "POST",
      body: formData,
    });
  },
  getAdminStats: () => request<AdminStats>("/admin/stats"),
  getAdminProducts: () => request<AdminProduct[]>("/admin/products"),
  uploadAdminProductImage: (image: File) => {
    const formData = new FormData();
    formData.set("image", image);
    return request<AdminUploadedImage>("/admin/products/image-upload", {
      method: "POST",
      body: formData,
    });
  },
  createAdminProduct: (payload: AdminProductPayload) =>
    request<AdminProduct>("/admin/products", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateAdminProduct: (productId: number, payload: AdminProductPayload) =>
    request<AdminProduct>(`/admin/products/${productId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteAdminProduct: (productId: number) =>
    request<{ message: string }>(`/admin/products/${productId}`, { method: "DELETE" }),
  toggleAdminProduct: (productId: number) =>
    request<{ message: string }>(`/admin/products/${productId}/toggle`, { method: "POST" }),
  getAdminPromotions: () => request<AdminPromotion[]>("/admin/promotions"),
  createAdminPromotion: (payload: {
    title: string;
    slug: string;
    description: string;
    image_url?: string | null;
    badge_text?: string | null;
    discount_type: "percent" | "fixed";
    discount_value: string;
    is_sitewide: boolean;
    is_active: boolean;
    product_ids: number[];
  }) =>
    request<AdminPromotion>("/admin/promotions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  toggleAdminPromotion: (promotionId: number) =>
    request<{ message: string }>(`/admin/promotions/${promotionId}/toggle`, { method: "POST" }),
  getAdminPromoCodes: () => request<AdminPromoCode[]>("/admin/promo-codes"),
  createAdminPromoCode: (payload: AdminPromoCodePayload) =>
    request<AdminPromoCode>("/admin/promo-codes", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateAdminPromoCode: (promoCodeId: number, payload: AdminPromoCodePayload) =>
    request<AdminPromoCode>(`/admin/promo-codes/${promoCodeId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  toggleAdminPromoCode: (promoCodeId: number) =>
    request<{ message: string }>(`/admin/promo-codes/${promoCodeId}/toggle`, { method: "POST" }),
  getAdminChannelPosts: () => request<AdminChannelPost[]>("/admin/channel/posts"),
  getAdminPaymentTickets: () => request<AdminPaymentTicket[]>("/admin/payment-tickets"),
  confirmAdminPaymentTicket: (ticketId: number) =>
    request<AdminPaymentTicket>(`/admin/payment-tickets/${ticketId}/confirm`, { method: "POST" }),
  rejectAdminPaymentTicket: (ticketId: number) =>
    request<AdminPaymentTicket>(`/admin/payment-tickets/${ticketId}/reject`, { method: "POST" }),
  getAdminPaymentSettings: () => request<AdminPaymentSettings>("/admin/settings/payment"),
  updateAdminPaymentSettings: (payload: AdminPaymentSettings) =>
    request<AdminPaymentSettings>("/admin/settings/payment", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  publishAdminProduct: (productId: number) =>
    request<AdminChannelPost>(`/admin/channel/products/${productId}/publish`, { method: "POST" }),
  publishAdminPromotion: (promotionId: number) =>
    request<AdminChannelPost>(`/admin/channel/promotions/${promotionId}/publish`, { method: "POST" }),
};
