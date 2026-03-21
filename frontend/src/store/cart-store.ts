import { create } from "zustand";

import type { Cart } from "types/api";
import { api } from "utils/api";
import { triggerLightHaptic, triggerSuccessHaptic } from "utils/telegram";

type CartState = {
  cart: Cart | null;
  loading: boolean;
  error: string | null;
  promoCode: string;
  fetchCart: (promoCodeOverride?: string) => Promise<void>;
  setPromoCode: (value: string) => void;
  applyPromoCode: () => Promise<void>;
  addToCart: (productId: number, packSizeId: number | null, qty?: number) => Promise<void>;
  updateQty: (cartItemId: number, qty: number) => Promise<void>;
  removeItem: (cartItemId: number) => Promise<void>;
  resetCart: () => void;
};

export const useCartStore = create<CartState>((set, get) => ({
  cart: null,
  loading: false,
  error: null,
  promoCode: "",
  fetchCart: async (promoCodeOverride) => {
    set({ loading: true, error: null });
    try {
      const promoCode = promoCodeOverride ?? get().promoCode.trim();
      const cart = await api.getCart(promoCode || undefined);
      set({ cart, loading: false, promoCode });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Не удалось загрузить корзину.",
        loading: false,
      });
    }
  },
  setPromoCode: (value) => set({ promoCode: value }),
  applyPromoCode: async () => {
    await get().fetchCart(get().promoCode);
  },
  addToCart: async (productId, packSizeId, qty = 1) => {
    triggerLightHaptic();
    await api.addToCart(productId, packSizeId, qty);
    triggerSuccessHaptic();
    await get().fetchCart();
  },
  updateQty: async (cartItemId, qty) => {
    if (qty <= 0) {
      await get().removeItem(cartItemId);
      return;
    }
    await api.updateCart(cartItemId, qty);
    await get().fetchCart();
  },
  removeItem: async (cartItemId) => {
    await api.removeFromCart(cartItemId);
    await get().fetchCart();
  },
  resetCart: () => set({ cart: null, promoCode: "", error: null }),
}));
