import { Copy, CreditCard, ImageUp, MessageSquareMore, ShieldCheck } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { EmptyState } from "components/common/EmptyState";
import type { CheckoutPaymentConfig } from "types/api";
import { useCartStore } from "store/cart-store";
import { api } from "utils/api";
import { formatPrice } from "utils/format";
import { getTelegramUserName, triggerSuccessHaptic } from "utils/telegram";

export function CheckoutPage() {
  const navigate = useNavigate();
  const { cart, promoCode, fetchCart, resetCart } = useCartStore();
  const [checkoutConfig, setCheckoutConfig] = useState<CheckoutPaymentConfig | null>(null);
  const [name, setName] = useState(getTelegramUserName());
  const [phone, setPhone] = useState("");
  const [customerContact, setCustomerContact] = useState("");
  const [comment, setComment] = useState("");
  const [deliveryType, setDeliveryType] = useState<"pickup" | "city_delivery">("pickup");
  const [paymentScreenshot, setPaymentScreenshot] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!cart) void fetchCart();
  }, [cart, fetchCart]);

  useEffect(() => {
    let active = true;

    async function loadConfig() {
      try {
        const response = await api.getCheckoutPaymentConfig();
        if (active) {
          setCheckoutConfig(response);
          setCustomerContact((current) => current || phone || "");
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Не удалось загрузить реквизиты оплаты.");
        }
      }
    }

    void loadConfig();
    return () => {
      active = false;
    };
  }, []);

  if (!cart || cart.items.length === 0) {
    return (
      <EmptyState
        title="Оформлять пока нечего"
        description="Сначала добавьте товары в корзину, затем вернитесь к оплате."
      />
    );
  }

  const handleCopyCard = async () => {
    if (!checkoutConfig?.card_number || !navigator.clipboard) return;
    await navigator.clipboard.writeText(checkoutConfig.card_number.replace(/\s+/g, ""));
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const normalizedContact = customerContact.trim();
    if (!paymentScreenshot) {
      setError("Прикрепите скриншот перевода, чтобы отправить тикет на проверку.");
      return;
    }
    if (normalizedContact.replace(/\s+/g, "").length < 3 || normalizedContact === "+" || normalizedContact === "@") {
      setError("Укажите телефон или @telegram для связи по оплате.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const order = await api.createPaymentTicket({
        customer_name: name,
        customer_phone: phone,
        customer_contact: normalizedContact,
        comment,
        delivery_type: deliveryType,
        promo_code: promoCode || undefined,
        payment_screenshot: paymentScreenshot,
      });
      resetCart();
      triggerSuccessHaptic();
      navigate(`/order/${order.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось отправить тикет оплаты.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <section className="glass-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-tea-700/70">оплата по чеку</p>
        <h2 className="font-display text-[2.1rem] font-semibold text-tea-900">Оплатите заказ и отправьте тикет</h2>
        <p className="mt-2 text-sm leading-6 text-fog">
          После перевода мы получим чек, сверим сумму и подтвердим заказ. Интерфейс оформления остался прежним,
          но теперь вместо мгновенной оплаты работает удобный ручной тикет.
        </p>
      </section>

      <section className="glass-card space-y-4 p-5">
        <div className="flex items-start gap-3">
          <div className="rounded-full bg-bark-100 p-3 text-bark-700">
            <CreditCard className="h-4 w-4" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-tea-900">Реквизиты оплаты</p>
            <p className="mt-1 text-xs leading-6 text-fog">
              Переведите ровно <span className="font-semibold text-tea-900">{formatPrice(cart.total)}</span> и
              прикрепите скриншот перевода ниже.
            </p>
          </div>
        </div>

        <div className="rounded-[1.6rem] border border-white/10 bg-black/20 p-4 shadow-soft">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-bark-500">карта для оплаты</p>
              <p className="mt-2 text-2xl font-extrabold tracking-[0.08em] text-tea-900">
                {checkoutConfig?.card_number ?? "Загружаем..."}
              </p>
              {checkoutConfig?.card_holder ? (
                <p className="mt-2 text-sm font-medium text-fog">{checkoutConfig.card_holder}</p>
              ) : null}
            </div>
            <button
              type="button"
              onClick={() => void handleCopyCard()}
              className="pressable rounded-full border border-tea-900/10 px-4 py-2 text-xs font-semibold text-tea-900"
            >
              <Copy className="mr-2 inline h-3.5 w-3.5" />
              {copied ? "Скопировано" : "Скопировать"}
            </button>
          </div>
          <p className="mt-3 text-sm leading-6 text-fog">
            {checkoutConfig?.instruction ?? "Подготавливаем инструкцию по оплате..."}
          </p>
        </div>
      </section>

      <form onSubmit={handleSubmit} className="glass-card space-y-4 p-5">
        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-tea-900">Имя</span>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
            minLength={3}
            className="w-full rounded-[1.25rem] border border-white/10 bg-black/10 px-4 py-3 text-tea-900 outline-none"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-tea-900">Телефон</span>
          <input
            value={phone}
            onChange={(event) => {
              setPhone(event.target.value);
              if (!customerContact) setCustomerContact(event.target.value);
            }}
            required
            className="w-full rounded-[1.25rem] border border-white/10 bg-black/10 px-4 py-3 text-tea-900 outline-none"
            placeholder="+998 90 000 00 00"
          />
        </label>

        <label className="block">
          <span className="mb-2 flex items-center gap-2 text-sm font-semibold text-tea-900">
            <MessageSquareMore className="h-4 w-4 text-bark-700" />
            Контакт для связи по оплате
          </span>
          <input
            value={customerContact}
            onChange={(event) => setCustomerContact(event.target.value)}
            required
            className="w-full rounded-[1.25rem] border border-white/10 bg-black/10 px-4 py-3 text-tea-900 outline-none"
            placeholder={checkoutConfig?.contact_hint ?? "Телефон или @telegram"}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-tea-900">Комментарий</span>
          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            rows={4}
            className="w-full rounded-[1.25rem] border border-white/10 bg-black/10 px-4 py-3 text-tea-900 outline-none"
            placeholder="Например, удобное время для связи или пожелания по заказу"
          />
        </label>

        <div>
          <p className="mb-2 text-sm font-semibold text-tea-900">Способ получения</p>
          <div className="grid grid-cols-1 gap-3">
            <button
              type="button"
              onClick={() => setDeliveryType("pickup")}
              className={`pressable rounded-[1.5rem] border px-4 py-4 text-left ${
                deliveryType === "pickup" ? "border-bark-500 bg-bark-100/70" : "border-white/10 bg-black/10"
              }`}
            >
              <p className="font-bold text-tea-900">Самовывоз</p>
              <p className="mt-1 text-sm text-fog">Подтвердим адрес и время выдачи после проверки оплаты.</p>
            </button>
            <button
              type="button"
              onClick={() => setDeliveryType("city_delivery")}
              className={`pressable rounded-[1.5rem] border px-4 py-4 text-left ${
                deliveryType === "city_delivery" ? "border-bark-500 bg-bark-100/70" : "border-white/10 bg-black/10"
              }`}
            >
              <p className="font-bold text-tea-900">Доставка по городу</p>
              <p className="mt-1 text-sm text-fog">Менеджер уточнит стоимость и время доставки после подтверждения.</p>
            </button>
          </div>
        </div>

        <label className="block">
          <span className="mb-2 flex items-center gap-2 text-sm font-semibold text-tea-900">
            <ImageUp className="h-4 w-4 text-bark-700" />
            Скриншот перевода
          </span>
          <label className="flex cursor-pointer items-center justify-center gap-3 rounded-[1.5rem] border border-dashed border-bark-500/40 bg-black/10 px-4 py-5 text-center">
            <ImageUp className="h-5 w-5 text-bark-700" />
            <div>
              <p className="text-sm font-semibold text-tea-900">
                {paymentScreenshot ? paymentScreenshot.name : "Выберите изображение чека"}
              </p>
              <p className="mt-1 text-xs text-fog">PNG, JPG или WEBP. Скриншот уйдет админам вместе с тикетом.</p>
            </div>
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="hidden"
              onChange={(event) => setPaymentScreenshot(event.target.files?.[0] ?? null)}
            />
          </label>
        </label>

        <div className="rounded-[1.5rem] bg-bark-100/75 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-fog">Товаров</span>
            <span className="text-sm font-semibold text-tea-900">{cart.total_items}</span>
          </div>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-sm text-fog">Подытог</span>
            <span className="text-sm font-semibold text-tea-900">{formatPrice(cart.subtotal)}</span>
          </div>
          {Number(cart.discount_amount) > 0 ? (
            <div className="mt-2 flex items-center justify-between">
              <span className="text-sm text-fog">Скидка</span>
              <span className="text-sm font-semibold text-bark-700">-{formatPrice(cart.discount_amount)}</span>
            </div>
          ) : null}
          {cart.promo_code ? (
            <div className="mt-2 flex items-center justify-between">
              <span className="text-sm text-fog">Промокод</span>
              <span className="text-sm font-semibold text-tea-900">{cart.promo_code}</span>
            </div>
          ) : null}
          <div className="mt-3 flex items-center justify-between">
            <span className="text-lg font-bold text-tea-900">К оплате</span>
            <span className="text-2xl font-extrabold text-tea-900">{formatPrice(cart.total)}</span>
          </div>
        </div>

        {error ? <p className="text-sm font-medium text-red-500">{error}</p> : null}

        <button
          type="submit"
          disabled={submitting}
          className="pressable w-full rounded-full bg-tea-900 px-5 py-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          <ShieldCheck className="mr-2 inline h-4 w-4" />
          {submitting ? "Отправляем тикет..." : "Отправить чек на проверку"}
        </button>
      </form>
    </div>
  );
}
