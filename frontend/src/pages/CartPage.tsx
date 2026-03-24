import { ShoppingBag, TicketPercent } from "lucide-react";
import { useEffect } from "react";
import { Link } from "react-router-dom";

import { QuantityControl } from "components/catalog/QuantityControl";
import { EmptyState } from "components/common/EmptyState";
import { ProductSkeleton } from "components/skeletons/ProductSkeleton";
import { useCartStore } from "store/cart-store";
import { formatPrice } from "utils/format";
import { resolveMediaUrl } from "utils/runtime-config";
import { buildTelegramMiniAppUrl, isTelegramMiniApp } from "utils/telegram";

export function CartPage() {
  const { cart, loading, error, promoCode, fetchCart, setPromoCode, applyPromoCode, updateQty, removeItem } = useCartStore();
  const inTelegram = isTelegramMiniApp();

  useEffect(() => {
    if (!inTelegram) return;
    if (!cart) void fetchCart();
  }, [cart, fetchCart, inTelegram]);

  if (!inTelegram) {
    return (
      <EmptyState
        title="Корзина работает в Telegram"
        description="В браузере можно смотреть каталог, а оформление заказа, корзина и промокоды доступны внутри Mini App."
        action={
          <a
            href={buildTelegramMiniAppUrl("cart")}
            target="_blank"
            rel="noreferrer"
            className="pressable rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white"
          >
            Перейти в Telegram
          </a>
        }
      />
    );
  }

  if (loading && !cart) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }).map((_, index) => (
          <ProductSkeleton key={index} />
        ))}
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <EmptyState
        title="Корзина пока пуста"
        description="Добавьте несколько позиций из каталога, и здесь появится ваш заказ."
        action={
          <Link to="/catalog" className="pressable rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white">
            Перейти в каталог
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-5">
      <div className="glass-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-tea-700/60">корзина</p>
        <h2 className="font-display text-[2.1rem] font-semibold text-tea-900">Ваш чайный заказ</h2>
        <p className="mt-2 text-sm leading-6 text-fog">Меняйте фасовки через карточку товара, количество прямо здесь и применяйте промокод перед оформлением.</p>
      </div>

      <section className="glass-card p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-bark-100 p-3 text-bark-700">
            <TicketPercent className="h-4 w-4" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-tea-900">Промокод</p>
            <p className="text-xs text-fog">Скидка может действовать на весь заказ или на отдельные товары.</p>
          </div>
        </div>
        <div className="mt-4 flex gap-3">
          <input
            value={promoCode}
            onChange={(event) => setPromoCode(event.target.value.toUpperCase())}
            className="w-full rounded-[1.25rem] border border-white/70 bg-white px-4 py-3 outline-none"
            placeholder="Например, TEA10"
          />
          <button
            type="button"
            onClick={() => void applyPromoCode()}
            className="pressable rounded-[1.25rem] bg-tea-900 px-4 py-3 text-sm font-semibold text-white"
          >
            Применить
          </button>
        </div>
        {error ? <p className="mt-3 text-sm font-medium text-red-500">{error}</p> : null}
        {cart.promo_code ? (
          <p className="mt-3 text-sm font-semibold text-tea-900">
            Активен промокод {cart.promo_code}
            {cart.promo_code_title ? ` — ${cart.promo_code_title}` : ""}
          </p>
        ) : null}
      </section>

      {cart.items.map((item) => (
        <article key={item.id} className="glass-card flex gap-4 p-4">
          <img src={resolveMediaUrl(item.product.image_url)} alt={item.product.name} className="h-28 w-24 rounded-[1.4rem] object-cover" />
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-tea-900">{item.product.name}</h3>
                <p className="mt-1 text-xs font-semibold uppercase tracking-[0.16em] text-bark-700">{item.pack_size.label}</p>
                <p className="mt-2 text-sm text-fog">{item.product.short_description}</p>
              </div>
              <button
                type="button"
                onClick={() => void removeItem(item.id)}
                className="pressable text-xs font-semibold text-bark-700"
              >
                Удалить
              </button>
            </div>
            <div className="mt-auto flex items-end justify-between gap-3 pt-4">
              <div>
                <p className="text-sm font-semibold text-fog">{formatPrice(item.pack_size.price)}</p>
                <p className="text-lg font-extrabold text-tea-900">{formatPrice(item.item_total)}</p>
              </div>
              <QuantityControl
                value={item.qty}
                onDecrease={() => void updateQty(item.id, item.qty - 1)}
                onIncrease={() => void updateQty(item.id, item.qty + 1)}
              />
            </div>
          </div>
        </article>
      ))}

      <section className="glass-card p-5">
        <div className="flex items-center justify-between">
          <span className="text-sm text-fog">Подытог</span>
          <span className="text-sm font-semibold text-tea-900">{formatPrice(cart.subtotal)}</span>
        </div>
        {Number(cart.discount_amount) > 0 ? (
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-fog">Скидка</span>
            <span className="text-sm font-semibold text-bark-700">-{formatPrice(cart.discount_amount)}</span>
          </div>
        ) : null}
        <div className="mt-3 flex items-center justify-between">
          <span className="text-lg font-bold text-tea-900">Итого</span>
          <span className="text-2xl font-extrabold text-tea-900">{formatPrice(cart.total)}</span>
        </div>
        <Link
          to="/checkout"
          className="pressable mt-5 flex w-full items-center justify-center rounded-full bg-tea-900 px-5 py-4 text-sm font-semibold text-white"
        >
          <ShoppingBag className="mr-2 h-4 w-4" />
          Оформить заказ
        </Link>
      </section>
    </div>
  );
}
