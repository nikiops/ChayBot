import { useEffect } from "react";
import { Link } from "react-router-dom";

import { ProductCard } from "components/catalog/ProductCard";
import { EmptyState } from "components/common/EmptyState";
import { ProductSkeleton } from "components/skeletons/ProductSkeleton";
import { useFavoritesStore } from "store/favorites-store";

export function FavoritesPage() {
  const { items, loading, fetchFavorites } = useFavoritesStore();

  useEffect(() => {
    if (items.length === 0) void fetchFavorites();
  }, [items.length, fetchFavorites]);

  if (loading && items.length === 0) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }).map((_, index) => (
          <ProductSkeleton key={index} />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="Избранное пока пусто"
        description="Отмечайте позиции сердцем на карточках товара, чтобы быстро возвращаться к ним позже."
        action={
          <Link to="/catalog" className="pressable rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white">
            Смотреть каталог
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-5">
      <section className="glass-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-tea-700/60">избранное</p>
        <h2 className="font-display text-[2.1rem] font-semibold text-tea-900">Сохранённые позиции</h2>
      </section>
      <div className="grid grid-cols-1 gap-4">
        {items.map((item) => (
          <ProductCard key={item.id} product={item.product} />
        ))}
      </div>
    </div>
  );
}

