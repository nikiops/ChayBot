import { create } from "zustand";

import type { Favorite } from "types/api";
import { api } from "utils/api";

type FavoritesState = {
  items: Favorite[];
  loading: boolean;
  fetchFavorites: () => Promise<void>;
  toggleFavorite: (productId: number) => Promise<void>;
  isFavorite: (productId: number) => boolean;
};

export const useFavoritesStore = create<FavoritesState>((set, get) => ({
  items: [],
  loading: false,
  fetchFavorites: async () => {
    set({ loading: true });
    try {
      const items = await api.getFavorites();
      set({ items, loading: false });
    } catch {
      set({ items: [], loading: false });
    }
  },
  toggleFavorite: async (productId) => {
    await api.toggleFavorite(productId);
    await get().fetchFavorites();
  },
  isFavorite: (productId) => get().items.some((item) => item.product.id === productId),
}));

