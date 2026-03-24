import { Heart, ShoppingBag } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { QuantityControl } from "components/catalog/QuantityControl";
import { EmptyState } from "components/common/EmptyState";
import { ProductSkeleton } from "components/skeletons/ProductSkeleton";
import type { Product, ProductPackSize } from "types/api";
import { useCartStore } from "store/cart-store";
import { useFavoritesStore } from "store/favorites-store";
import { api } from "utils/api";
import { formatPrice } from "utils/format";
import { resolveMediaUrl } from "utils/runtime-config";
import { buildTelegramMiniAppUrl, isTelegramMiniApp } from "utils/telegram";

export function ProductPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const addToCart = useCartStore((state) => state.addToCart);
  const toggleFavorite = useFavoritesStore((state) => state.toggleFavorite);
  const isFavorite = useFavoritesStore((state) => state.isFavorite);
  const [product, setProduct] = useState<Product | null>(null);
  const [selectedPackId, setSelectedPackId] = useState<number | null>(null);
  const [qty, setQty] = useState(1);
  const [loading, setLoading] = useState(true);
  const inTelegram = isTelegramMiniApp();

  useEffect(() => {
    if (!slug) return;
    const productSlug = slug;
    let active = true;

    async function load() {
      setLoading(true);
      try {
        const response = await api.getProduct(productSlug);
        if (!active) return;
        setProduct(response);
        setSelectedPackId(response.default_pack_size.id);
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [slug]);

  const selectedPack = useMemo<ProductPackSize | null>(() => {
    if (!product) return null;
    return product.pack_sizes.find((item) => item.id === selectedPackId) ?? product.default_pack_size;
  }, [product, selectedPackId]);

  useEffect(() => {
    setQty(1);
  }, [selectedPackId]);

  if (loading) {
    return <ProductSkeleton />;
  }

  if (!product || !selectedPack) {
    return (
      <EmptyState
        title="Товар не найден"
        description="Позиция могла быть скрыта или перемещена в другую подборку."
      />
    );
  }

  const telegramUrl = buildTelegramMiniAppUrl(`product:${product.slug}`);

  return (
    <div className="space-y-5">
      <div className="glass-card overflow-hidden">
        <div className="relative">
          <img src={resolveMediaUrl(product.image_url)} alt={product.name} className="h-[320px] w-full object-cover" />
          {selectedPack.discount_percent ? (
            <span className="absolute left-4 top-4 rounded-full bg-bark-500 px-3 py-1 text-sm font-bold text-white">
              -{selectedPack.discount_percent}%
            </span>
          ) : null}
          <button
            type="button"
            onClick={() => void toggleFavorite(product.id)}
            className={`pressable absolute right-4 top-4 rounded-full border border-white/60 p-3 backdrop-blur-sm ${
              isFavorite(product.id) ? "bg-tea-900 text-white" : "bg-white/80 text-tea-900"
            }`}
          >
            <Heart className={`h-5 w-5 ${isFavorite(product.id) ? "fill-current" : ""}`} />
          </button>
        </div>
        <div className="space-y-5 p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-tea-700/60">{product.category?.name}</p>
            <h2 className="mt-2 font-display text-[2.4rem] font-semibold leading-[0.92] text-tea-900">{product.name}</h2>
            <p className="mt-4 text-sm leading-7 text-fog">{product.full_description}</p>
          </div>

          <div className="flex items-end gap-3">
            <span className="text-3xl font-extrabold text-tea-900">{formatPrice(selectedPack.price)}</span>
            {selectedPack.old_price ? <span className="pb-1 text-lg text-fog line-through">{formatPrice(selectedPack.old_price)}</span> : null}
          </div>

          <div className="space-y-3">
            <p className="text-sm font-semibold text-tea-900">Фасовка</p>
            <div className="grid grid-cols-3 gap-3">
              {product.pack_sizes.map((pack) => (
                <button
                  key={`${pack.id ?? pack.label}`}
                  type="button"
                  onClick={() => setSelectedPackId(pack.id)}
                  className={`pressable rounded-[1.35rem] border px-3 py-3 text-left ${
                    selectedPack.id === pack.id ? "border-tea-900 bg-tea-100" : "border-white/70 bg-white"
                  }`}
                >
                  <p className="text-sm font-bold text-tea-900">{pack.label}</p>
                  <p className="mt-1 text-xs text-fog">{formatPrice(pack.price)}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-[1.75rem] bg-tea-100 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-tea-700/60">наличие</p>
              <p className="mt-2 text-sm font-bold text-tea-900">
                {selectedPack.is_in_stock ? `Осталось ${selectedPack.stock_qty} шт.` : "Временно нет"}
              </p>
            </div>
            <div className="rounded-[1.75rem] bg-bark-100 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-bark-700/60">формат</p>
              <p className="mt-2 text-sm font-bold text-tea-900">
                {selectedPack.weight_grams ? `${selectedPack.weight_grams} г для спокойных чаепитий` : "Подарочный или штучный формат"}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-fog">Количество</p>
              <p className="text-xs text-fog">Измените перед добавлением в корзину</p>
            </div>
            <QuantityControl
              value={qty}
              onDecrease={() => setQty((current) => Math.max(1, current - 1))}
              onIncrease={() => setQty((current) => Math.min(selectedPack.stock_qty, current + 1))}
            />
          </div>

          {inTelegram ? (
            <div className="grid grid-cols-1 gap-3">
              <button
                type="button"
                disabled={!selectedPack.is_in_stock}
                onClick={() => void addToCart(product.id, selectedPack.id, qty)}
                className="pressable rounded-full bg-tea-900 px-5 py-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                <ShoppingBag className="mr-2 inline h-4 w-4" />
                Добавить в корзину
              </button>
              <button
                type="button"
                disabled={!selectedPack.is_in_stock}
                onClick={async () => {
                  await addToCart(product.id, selectedPack.id, qty);
                  navigate("/cart");
                }}
                className="pressable rounded-full bg-bark-100 px-5 py-4 text-sm font-semibold text-bark-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Купить сейчас
              </button>
            </div>
          ) : (
            <div className="space-y-3 rounded-[1.5rem] border border-white/10 bg-white/8 p-4">
              <p className="text-sm leading-6 text-[#ead9b6]/86">
                Оформление заказа работает в Telegram Mini App. Откройте товар в боте, и корзина с оформлением будут доступны сразу.
              </p>
              <a
                href={telegramUrl}
                target="_blank"
                rel="noreferrer"
                className="pressable inline-flex w-full items-center justify-center rounded-full bg-tea-900 px-5 py-4 text-sm font-semibold text-white"
              >
                Открыть в Telegram
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
