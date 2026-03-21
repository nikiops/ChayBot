import { ExternalLink, ReceiptText } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { EmptyState } from "components/common/EmptyState";
import type { Order } from "types/api";
import { api } from "utils/api";
import { formatDeliveryType, formatOrderStatus, formatPaymentTicketStatus, formatPrice } from "utils/format";
import { resolveMediaUrl } from "utils/runtime-config";

export function OrderPage() {
  const { id } = useParams();
  const [order, setOrder] = useState<Order | null>(null);

  useEffect(() => {
    const orderId: string = id ?? "";
    if (!orderId) return;
    let active = true;

    async function load() {
      const response = await api.getOrder(orderId);
      if (active) setOrder(response);
    }

    void load();
    return () => {
      active = false;
    };
  }, [id]);

  if (!order) {
    return <EmptyState title="Загружаем заказ" description="Получаем состав заказа, тикет оплаты и текущий статус." />;
  }

  const ticket = order.payment_ticket;
  const screenshotUrl = resolveMediaUrl(ticket?.screenshot_path);
  const heroTitle = order.status === "confirmed" ? "Оплата подтверждена" : order.status === "cancelled" ? "Тикет отклонен" : "Чек отправлен на проверку";
  const heroDescription =
    order.status === "confirmed"
      ? `Заказ #${order.id} подтвержден. Можно ожидать связь менеджера для финального согласования деталей.`
      : order.status === "cancelled"
        ? `Тикет по заказу #${order.id} был отклонен. Откройте чек, проверьте сумму и при необходимости свяжитесь с магазином.`
        : `Заказ #${order.id} уже сохранен в системе. Как только администратор проверит перевод, статус изменится на подтвержденный.`;

  return (
    <div className="space-y-5">
      <section className="glass-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-tea-700/70">заказ сохранен</p>
        <h2 className="font-display text-[2.2rem] font-semibold text-tea-900">{heroTitle}</h2>
        <p className="mt-3 text-sm leading-6 text-fog">{heroDescription}</p>
      </section>

      <section className="glass-card p-5">
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm text-fog">Статус</span>
          <span className="rounded-full bg-bark-100 px-3 py-1 text-sm font-semibold text-bark-700">
            {formatOrderStatus(order.status)}
          </span>
        </div>
        {ticket ? (
          <div className="mt-3 flex items-center justify-between gap-3">
            <span className="text-sm text-fog">Тикет оплаты</span>
            <span className="rounded-full bg-black/10 px-3 py-1 text-sm font-semibold text-tea-900">
              {formatPaymentTicketStatus(ticket.status)}
            </span>
          </div>
        ) : null}
        <div className="mt-3 flex items-center justify-between">
          <span className="text-sm text-fog">Получение</span>
          <span className="text-sm font-semibold text-tea-900">{formatDeliveryType(order.delivery_type)}</span>
        </div>
        {order.promo_code ? (
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-fog">Промокод</span>
            <span className="text-sm font-semibold text-tea-900">{order.promo_code}</span>
          </div>
        ) : null}
        <div className="mt-3 flex items-center justify-between">
          <span className="text-sm text-fog">Подытог</span>
          <span className="text-sm font-semibold text-tea-900">{formatPrice(order.subtotal_amount)}</span>
        </div>
        {Number(order.discount_amount) > 0 ? (
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-fog">Скидка</span>
            <span className="text-sm font-semibold text-bark-700">-{formatPrice(order.discount_amount)}</span>
          </div>
        ) : null}
        <div className="mt-3 flex items-center justify-between">
          <span className="text-sm text-fog">Итого</span>
          <span className="text-xl font-extrabold text-tea-900">{formatPrice(order.total_amount)}</span>
        </div>
      </section>

      {ticket ? (
        <section className="glass-card p-5">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-bark-100 p-3 text-bark-700">
              <ReceiptText className="h-4 w-4" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-tea-900">Тикет оплаты</h3>
              <p className="mt-1 text-sm leading-6 text-fog">
                Мы получили ваш чек и контакт для связи. Если понадобится уточнение, менеджер напишет по указанному
                номеру или Telegram.
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-[1.5rem] bg-black/10 p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-fog">Сумма перевода</span>
              <span className="text-sm font-semibold text-tea-900">{formatPrice(ticket.payment_amount)}</span>
            </div>
            <div className="mt-3 flex items-center justify-between">
              <span className="text-sm text-fog">Контакт</span>
              <span className="text-sm font-semibold text-tea-900">{ticket.customer_contact}</span>
            </div>
            <div className="mt-3 flex items-center justify-between">
              <span className="text-sm text-fog">Карта</span>
              <span className="text-sm font-semibold text-tea-900">{ticket.payment_card_number}</span>
            </div>
            {ticket.admin_comment ? (
              <div className="mt-3 rounded-[1.2rem] bg-bark-100/70 px-4 py-3 text-sm text-tea-900">
                Комментарий администратора: {ticket.admin_comment}
              </div>
            ) : null}
          </div>

          {screenshotUrl ? (
            <a
              href={screenshotUrl}
              target="_blank"
              rel="noreferrer"
              className="pressable mt-4 inline-flex items-center rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white"
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Открыть загруженный чек
            </a>
          ) : null}
        </section>
      ) : null}

      <section className="glass-card p-5">
        <h3 className="text-lg font-bold text-tea-900">Состав заказа</h3>
        <div className="mt-4 space-y-3">
          {order.items.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-3 rounded-[1.25rem] bg-black/10 px-4 py-3">
              <div>
                <p className="font-semibold text-tea-900">{item.product_name}</p>
                <p className="text-sm text-fog">
                  {item.pack_label ? `${item.pack_label} • ` : ""}
                  {item.qty} шт. x {formatPrice(item.price)}
                </p>
              </div>
              <p className="font-bold text-tea-900">{formatPrice(item.item_total)}</p>
            </div>
          ))}
        </div>
        <Link to="/catalog" className="pressable mt-5 inline-flex rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white">
          Вернуться в каталог
        </Link>
      </section>
    </div>
  );
}
