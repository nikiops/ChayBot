import { Heart, ShoppingBag } from "lucide-react";
import { Link } from "react-router-dom";

import type { Product } from "types/api";
import { useCartStore } from "store/cart-store";
import { useFavoritesStore } from "store/favorites-store";
import { buildProductSubtitle, formatPrice } from "utils/format";
import { resolveMediaUrl } from "utils/runtime-config";

type ProductCardProps = {
  product: Product;
};

export function ProductCard({ product }: ProductCardProps) {
  const addToCart = useCartStore((state) => state.addToCart);
  const toggleFavorite = useFavoritesStore((state) => state.toggleFavorite);
  const isFavorite = useFavoritesStore((state) => state.isFavorite(product.id));

  return (
    <article className="glass-card overflow-hidden">
      <div className="relative">
        <img src={resolveMediaUrl(product.image_url)} alt={product.name} className="h-44 w-full object-cover" />
        <button
          type="button"
          onClick={() => void toggleFavorite(product.id)}
          className={`pressable absolute right-3 top-3 rounded-full border border-white/60 p-2 backdrop-blur-sm ${
            isFavorite ? "bg-tea-900 text-white" : "bg-white/80 text-tea-900"
          }`}
        >
          <Heart className={`h-4 w-4 ${isFavorite ? "fill-current" : ""}`} />
        </button>
        {product.discount_percent ? (
          <div className="absolute left-3 top-3 rounded-full bg-bark-500 px-3 py-1 text-xs font-bold text-white">
            -{product.discount_percent}%
          </div>
        ) : null}
      </div>
      <div className="p-4">
        <div className="mb-2 flex items-start justify-between gap-3">
          <div>
            <h3 className="text-base font-extrabold text-tea-900">{product.name}</h3>
            <p className="mt-2 text-sm leading-6 text-fog">{buildProductSubtitle(product.short_description)}</p>
          </div>
        </div>
        <div className="rounded-[1.2rem] bg-bark-100/60 px-3 py-2 text-xs font-semibold text-bark-700">
          от {product.default_pack_size.label}
        </div>
        <div className="mt-4 flex items-end justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-extrabold text-tea-900">{formatPrice(product.price)}</span>
              {product.old_price ? <span className="text-sm text-fog line-through">{formatPrice(product.old_price)}</span> : null}
            </div>
            <p className={`mt-1 text-xs font-semibold ${product.is_in_stock ? "text-tea-700" : "text-red-500"}`}>
              {product.is_in_stock ? "В наличии" : "Временно нет"}
            </p>
          </div>
          <div className="flex gap-2">
            <Link
              to={`/product/${product.slug}`}
              className="pressable rounded-full border border-tea-900/12 px-4 py-2 text-sm font-semibold text-tea-900"
            >
              Открыть
            </Link>
            <button
              type="button"
              disabled={!product.is_in_stock}
              onClick={() => void addToCart(product.id, product.default_pack_size.id, 1)}
              className="pressable rounded-full bg-tea-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              <ShoppingBag className="mr-1 inline h-4 w-4" />
              В корзину
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
