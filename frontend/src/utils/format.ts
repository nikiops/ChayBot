export function formatPrice(value: string | number) {
  const amount = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(amount)) return "0 сум";
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(amount)} сум`;
}

export function formatDeliveryType(value: string) {
  return value === "city_delivery" ? "Доставка по городу" : "Самовывоз";
}

export function buildProductSubtitle(text: string, limit = 92) {
  return text.length > limit ? `${text.slice(0, limit).trim()}...` : text;
}

export function formatOrderStatus(value: string) {
  if (value === "confirmed") return "Оплата подтверждена";
  if (value === "cancelled") return "Тикет отклонен";
  if (value === "completed") return "Заказ завершен";
  return "Чек на проверке";
}

export function formatPaymentTicketStatus(value: string) {
  if (value === "confirmed") return "Подтвержден";
  if (value === "rejected") return "Отклонен";
  return "На проверке";
}
