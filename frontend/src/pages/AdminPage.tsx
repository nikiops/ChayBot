import { useEffect, useState } from "react";

import { EmptyState } from "components/common/EmptyState";
import { ImagePlus, Trash2 } from "lucide-react";
import type {
  AdminChannelPost,
  AdminPaymentSettings,
  AdminPaymentTicket,
  AdminProduct,
  AdminPromoCode,
  AdminPromotion,
  AdminStats,
  Category,
} from "types/api";
import { api } from "utils/api";
import { formatPrice } from "utils/format";
import { resolveMediaUrl } from "utils/runtime-config";

type ProductPackFormState = {
  label: string;
  weight_grams: string;
  price: string;
  old_price: string;
  stock_qty: string;
  sort_order: string;
  is_default: boolean;
};

type ProductFormState = {
  category_id: string;
  name: string;
  slug: string;
  short_description: string;
  full_description: string;
  image_url: string;
  is_active: boolean;
  is_featured: boolean;
  pack_sizes: ProductPackFormState[];
};

type PromotionFormState = {
  title: string;
  slug: string;
  description: string;
  image_url: string;
  badge_text: string;
  discount_type: "percent" | "fixed";
  discount_value: string;
  is_sitewide: boolean;
  product_ids: string;
};

type PromoCodeFormState = {
  code: string;
  title: string;
  description: string;
  discount_type: "percent" | "fixed";
  discount_value: string;
  minimum_order_amount: string;
  max_uses: string;
  is_sitewide: boolean;
  is_active: boolean;
  product_ids: string;
};

type PaymentSettingsFormState = {
  card_number: string;
  card_holder: string;
  instruction: string;
  contact_hint: string;
};

const promotionInitialState: PromotionFormState = {
  title: "",
  slug: "",
  description: "",
  image_url: "",
  badge_text: "",
  discount_type: "percent",
  discount_value: "10",
  is_sitewide: true,
  product_ids: "",
};

const promoCodeInitialState: PromoCodeFormState = {
  code: "",
  title: "",
  description: "",
  discount_type: "percent",
  discount_value: "10",
  minimum_order_amount: "",
  max_uses: "",
  is_sitewide: true,
  is_active: true,
  product_ids: "",
};

const paymentSettingsInitialState: PaymentSettingsFormState = {
  card_number: "",
  card_holder: "",
  instruction: "",
  contact_hint: "",
};

const PRODUCT_IMAGE_MAX_SIZE_BYTES = 6 * 1024 * 1024;
const PRODUCT_IMAGE_ALLOWED_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);
const PRODUCT_IMAGE_MIN_WIDTH = 900;
const PRODUCT_IMAGE_MIN_HEIGHT = 900;
const PRODUCT_IMAGE_HINTS = [
  "Формат: JPG, PNG или WEBP",
  "Размер файла: до 6 МБ",
  "Рекомендуем от 1200x1200 px",
  "Лучше без текста у самых краев, карточка может слегка обрезать фото",
];

function createEmptyPack(defaultPack = false): ProductPackFormState {
  return { label: "", weight_grams: "", price: "", old_price: "", stock_qty: "0", sort_order: "0", is_default: defaultPack };
}

const productInitialState: ProductFormState = {
  category_id: "",
  name: "",
  slug: "",
  short_description: "",
  full_description: "",
  image_url: "",
  is_active: true,
  is_featured: false,
  pack_sizes: [createEmptyPack(true)],
};

function parseIds(value: string) {
  return value.split(",").map((item) => Number(item.trim())).filter((item) => Number.isFinite(item) && item > 0);
}

function stringifyIds(ids: number[]) {
  return ids.join(", ");
}

function productToForm(product: AdminProduct): ProductFormState {
  return {
    category_id: String(product.category_id),
    name: product.name,
    slug: product.slug,
    short_description: product.short_description,
    full_description: product.full_description,
    image_url: product.image_url,
    is_active: product.is_active,
    is_featured: product.is_featured,
    pack_sizes: product.pack_sizes.map((pack, index) => ({
      label: pack.label,
      weight_grams: pack.weight_grams ? String(pack.weight_grams) : "",
      price: String(pack.base_price ?? pack.price),
      old_price: pack.old_price ? String(pack.old_price) : "",
      stock_qty: String(pack.stock_qty),
      sort_order: String(pack.sort_order ?? index),
      is_default: pack.is_default,
    })),
  };
}

function promoCodeToForm(promoCode: AdminPromoCode): PromoCodeFormState {
  return {
    code: promoCode.code,
    title: promoCode.title,
    description: promoCode.description,
    discount_type: promoCode.discount_type,
    discount_value: String(promoCode.discount_value),
    minimum_order_amount: promoCode.minimum_order_amount ?? "",
    max_uses: promoCode.max_uses ? String(promoCode.max_uses) : "",
    is_sitewide: promoCode.is_sitewide,
    is_active: promoCode.is_active,
    product_ids: stringifyIds(promoCode.product_ids),
  };
}

function formatDateTime(value: string | null) {
  if (!value) return "Без ограничений";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

async function getImageDimensions(file: File): Promise<{ width: number; height: number }> {
  const objectUrl = URL.createObjectURL(file);
  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("Не удалось прочитать изображение."));
      img.src = objectUrl;
    });
    return { width: image.naturalWidth, height: image.naturalHeight };
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

export function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [promotions, setPromotions] = useState<AdminPromotion[]>([]);
  const [promoCodes, setPromoCodes] = useState<AdminPromoCode[]>([]);
  const [channelPosts, setChannelPosts] = useState<AdminChannelPost[]>([]);
  const [paymentTickets, setPaymentTickets] = useState<AdminPaymentTicket[]>([]);
  const [paymentSettings, setPaymentSettings] = useState<PaymentSettingsFormState>(paymentSettingsInitialState);
  const [productForm, setProductForm] = useState<ProductFormState>(productInitialState);
  const [promotionForm, setPromotionForm] = useState<PromotionFormState>(promotionInitialState);
  const [promoCodeForm, setPromoCodeForm] = useState<PromoCodeFormState>(promoCodeInitialState);
  const [editingProductId, setEditingProductId] = useState<number | null>(null);
  const [editingPromoCodeId, setEditingPromoCodeId] = useState<number | null>(null);
  const [productImageUploading, setProductImageUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [
        statsResponse,
        categoriesResponse,
        productsResponse,
        promotionsResponse,
        promoCodesResponse,
        channelPostsResponse,
        paymentTicketsResponse,
        paymentSettingsResponse,
      ] = await Promise.all([
        api.getAdminStats(),
        api.getCategories(),
        api.getAdminProducts(),
        api.getAdminPromotions(),
        api.getAdminPromoCodes(),
        api.getAdminChannelPosts(),
        api.getAdminPaymentTickets(),
        api.getAdminPaymentSettings(),
      ]);
      setStats(statsResponse);
      setCategories(categoriesResponse);
      setProducts(productsResponse);
      setPromotions(promotionsResponse);
      setPromoCodes(promoCodesResponse);
      setChannelPosts(channelPostsResponse);
      setPaymentTickets(paymentTicketsResponse);
      setPaymentSettings({
        card_number: paymentSettingsResponse.card_number,
        card_holder: paymentSettingsResponse.card_holder ?? "",
        instruction: paymentSettingsResponse.instruction,
        contact_hint: paymentSettingsResponse.contact_hint,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить админ-панель.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  async function runAction(action: () => Promise<void>) {
    setSubmitting(true);
    setError(null);
    setStatusMessage(null);
    try {
      await action();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Операция не выполнена.");
    } finally {
      setSubmitting(false);
    }
  }

  function resetProductForm() { setEditingProductId(null); setProductForm(productInitialState); }
  function resetPromoCodeForm() { setEditingPromoCodeId(null); setPromoCodeForm(promoCodeInitialState); }

  function updatePack(index: number, patch: Partial<ProductPackFormState>) {
    setProductForm((current) => ({
      ...current,
      pack_sizes: current.pack_sizes.map((pack, packIndex) => {
        if (packIndex !== index) return patch.is_default ? { ...pack, is_default: false } : pack;
        return { ...pack, ...patch };
      }),
    }));
  }

  function addPack() { setProductForm((current) => ({ ...current, pack_sizes: [...current.pack_sizes, createEmptyPack(false)] })); }

  function removePack(index: number) {
    setProductForm((current) => {
      const next = current.pack_sizes.filter((_, packIndex) => packIndex !== index);
      if (!next.length) return { ...current, pack_sizes: [createEmptyPack(true)] };
      if (!next.some((pack) => pack.is_default)) next[0] = { ...next[0], is_default: true };
      return { ...current, pack_sizes: next };
    });
  }

  async function handleProductImageUpload(file: File | null) {
    if (!file) return;
    if (!PRODUCT_IMAGE_ALLOWED_TYPES.has(file.type)) {
      throw new Error("Загрузите фото в формате JPG, PNG или WEBP.");
    }
    if (file.size > PRODUCT_IMAGE_MAX_SIZE_BYTES) {
      throw new Error("Фото слишком большое. Максимум 6 МБ.");
    }

    const { width, height } = await getImageDimensions(file);
    if (width < PRODUCT_IMAGE_MIN_WIDTH || height < PRODUCT_IMAGE_MIN_HEIGHT) {
      throw new Error("Изображение слишком маленькое. Минимум 900x900 px.");
    }

    setProductImageUploading(true);
    try {
      const uploaded = await api.uploadAdminProductImage(file);
      setProductForm((current) => ({ ...current, image_url: uploaded.image_url }));
      setStatusMessage(`Фото загружено: ${uploaded.file_name}.`);
    } finally {
      setProductImageUploading(false);
    }
  }

  async function submitProductForm() {
    if (!productForm.image_url.trim()) {
      throw new Error("Сначала загрузите фото товара.");
    }

    const payload = {
      category_id: Number(productForm.category_id),
      name: productForm.name.trim(),
      slug: productForm.slug.trim(),
      short_description: productForm.short_description.trim(),
      full_description: productForm.full_description.trim(),
      image_url: productForm.image_url.trim(),
      is_active: productForm.is_active,
      is_featured: productForm.is_featured,
      pack_sizes: productForm.pack_sizes.map((pack, index) => ({ label: pack.label.trim(), weight_grams: pack.weight_grams ? Number(pack.weight_grams) : null, price: pack.price, old_price: pack.old_price || null, stock_qty: Number(pack.stock_qty || 0), sort_order: Number(pack.sort_order || index), is_default: pack.is_default })),
    };
    if (editingProductId) {
      await api.updateAdminProduct(editingProductId, payload);
      setStatusMessage("Товар обновлен.");
    } else {
      await api.createAdminProduct(payload);
      setStatusMessage("Товар создан.");
    }
    resetProductForm();
  }

  async function submitPromoCodeForm() {
    const payload = { code: promoCodeForm.code.trim().toUpperCase(), title: promoCodeForm.title.trim(), description: promoCodeForm.description.trim(), discount_type: promoCodeForm.discount_type, discount_value: promoCodeForm.discount_value, is_sitewide: promoCodeForm.is_sitewide, minimum_order_amount: promoCodeForm.minimum_order_amount || null, max_uses: promoCodeForm.max_uses ? Number(promoCodeForm.max_uses) : null, is_active: promoCodeForm.is_active, product_ids: parseIds(promoCodeForm.product_ids) };
    if (editingPromoCodeId) {
      await api.updateAdminPromoCode(editingPromoCodeId, payload);
      setStatusMessage("Промокод обновлен.");
    } else {
      await api.createAdminPromoCode(payload);
      setStatusMessage("Промокод создан.");
    }
    resetPromoCodeForm();
  }

  async function submitPaymentSettingsForm() {
    const payload: AdminPaymentSettings = {
      card_number: paymentSettings.card_number.trim(),
      card_holder: paymentSettings.card_holder.trim() || null,
      instruction: paymentSettings.instruction.trim(),
      contact_hint: paymentSettings.contact_hint.trim(),
    };
    await api.updateAdminPaymentSettings(payload);
    setStatusMessage("Реквизиты оплаты обновлены.");
  }

  if (loading && !stats) {
    return <div className="glass-card p-6"><p className="text-sm text-fog">Загружаем админ-панель...</p></div>;
  }

  if (error && !stats) {
    return (
      <EmptyState
        title="Нет доступа к админ-панели"
        description={error}
        action={<button type="button" onClick={() => void load()} className="pressable rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white">Повторить</button>}
      />
    );
  }

  return (
    <div className="space-y-5">
      <section className="glass-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-tea-700/60">admin</p>
        <h2 className="font-display text-[2.1rem] font-semibold text-tea-900">Панель магазина</h2>
        <p className="mt-2 text-sm leading-6 text-fog">Управляйте товарами, фасовками, акциями, промокодами и публикациями в канал {channelPosts[0]?.channel_chat_id ?? "-1003357674923"}.</p>
        {error ? <p className="mt-3 text-sm font-medium text-red-500">{error}</p> : null}
        {statusMessage ? <p className="mt-3 text-sm font-medium text-tea-900">{statusMessage}</p> : null}
      </section>

      {stats ? (
        <section className="grid grid-cols-2 gap-3">
          {[["Пользователи", stats.users_count], ["Заказы", stats.orders_count], ["Товары", stats.products_count], ["Активные", stats.active_products_count], ["Акции", stats.promotions_count], ["Промокоды", stats.promo_codes_count], ["Тикеты", stats.payment_tickets_count], ["Новые чеки", stats.pending_payment_tickets_count]].map(([label, value]) => (
            <div key={label} className="glass-card p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-tea-700/60">{label}</p>
              <p className="mt-2 text-2xl font-extrabold text-tea-900">{value}</p>
            </div>
          ))}
        </section>
      ) : null}

      <section className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-tea-900">Реквизиты оплаты</h3>
            <p className="mt-1 text-sm text-fog">Эти данные видит покупатель на шаге оплаты перед загрузкой чека.</p>
          </div>
          <button type="button" disabled={submitting} onClick={() => void runAction(submitPaymentSettingsForm)} className="pressable rounded-full bg-tea-900 px-5 py-3 text-sm font-semibold text-white">Сохранить</button>
        </div>

        <div className="grid grid-cols-1 gap-3">
          <input value={paymentSettings.card_number} onChange={(event) => setPaymentSettings((current) => ({ ...current, card_number: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Номер карты" />
          <input value={paymentSettings.card_holder} onChange={(event) => setPaymentSettings((current) => ({ ...current, card_holder: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Имя владельца карты" />
          <textarea value={paymentSettings.instruction} onChange={(event) => setPaymentSettings((current) => ({ ...current, instruction: event.target.value }))} rows={3} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Инструкция по оплате" />
          <input value={paymentSettings.contact_hint} onChange={(event) => setPaymentSettings((current) => ({ ...current, contact_hint: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Подсказка для контакта покупателя" />
        </div>
      </section>

      <section className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-tea-900">Тикеты оплаты</h3>
            <p className="mt-1 text-sm text-fog">Здесь появляются скриншоты переводов. Подтверждение переводит заказ в статус confirmed.</p>
          </div>
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-fog">{paymentTickets.length} шт.</span>
        </div>
        <div className="space-y-3">
          {paymentTickets.length ? paymentTickets.map((ticket) => (
            <div key={ticket.id} className="rounded-[1.35rem] bg-white/70 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <p className="font-bold text-tea-900">Тикет #{ticket.id} • заказ #{ticket.order_id}</p>
                  <p className="text-sm text-fog">{ticket.customer_name} • {ticket.customer_phone} • {ticket.customer_contact}</p>
                  <p className="text-sm text-fog">Сумма: {formatPrice(ticket.payment_amount)} • Статус: {ticket.status}</p>
                  <p className="text-xs text-fog">Состав: {ticket.items_summary.join(", ") || "—"}</p>
                  <p className="text-xs text-fog">Создан: {formatDateTime(ticket.created_at)}</p>
                  {ticket.promo_code ? <p className="text-xs text-bark-700">Промокод: {ticket.promo_code}</p> : null}
                  {ticket.screenshot_path ? (
                    <a href={resolveMediaUrl(ticket.screenshot_path)} target="_blank" rel="noreferrer" className="inline-flex text-xs font-semibold text-bark-700">
                      Открыть чек
                    </a>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" disabled={submitting || ticket.status !== "new"} onClick={() => void runAction(async () => { await api.confirmAdminPaymentTicket(ticket.id); setStatusMessage(`Тикет #${ticket.id} подтвержден.`); })} className="pressable rounded-full bg-tea-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Подтвердить</button>
                  <button type="button" disabled={submitting || ticket.status !== "new"} onClick={() => void runAction(async () => { await api.rejectAdminPaymentTicket(ticket.id); setStatusMessage(`Тикет #${ticket.id} отклонен.`); })} className="pressable rounded-full border border-red-200 px-4 py-2 text-sm font-semibold text-red-500 disabled:opacity-50">Отклонить</button>
                </div>
              </div>
            </div>
          )) : <div className="rounded-[1.35rem] bg-white/70 p-4 text-sm text-fog">Новых тикетов оплаты пока нет.</div>}
        </div>
      </section>

      <section className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-tea-900">{editingProductId ? "Редактирование товара" : "Добавить товар"}</h3>
            <p className="mt-1 text-sm text-fog">Создавайте карточки чая и управляйте фасовками прямо из Mini App.</p>
          </div>
          {editingProductId ? <button type="button" onClick={resetProductForm} className="pressable rounded-full border border-tea-900/10 px-4 py-2 text-sm font-semibold text-tea-900">Новый товар</button> : null}
        </div>

        <div className="grid grid-cols-1 gap-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <select value={productForm.category_id} onChange={(event) => setProductForm((current) => ({ ...current, category_id: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none">
              <option value="">Выберите категорию</option>
              {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
            </select>
            <div className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-tea-900">Фото товара</p>
                  <p className="mt-1 text-xs text-fog">Загружайте файл вместо ссылки. Мы сохраним его в медиатеке магазина.</p>
                </div>
                <label className="pressable cursor-pointer rounded-full bg-tea-900 px-4 py-2 text-sm font-semibold text-white">
                  <ImagePlus className="mr-2 inline h-4 w-4" />
                  {productImageUploading ? "Загружаем..." : "Выбрать фото"}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="hidden"
                    disabled={productImageUploading || submitting}
                    onChange={(event) => {
                      const file = event.target.files?.[0] ?? null;
                      if (file) {
                        void runAction(async () => {
                          await handleProductImageUpload(file);
                        });
                      }
                      event.currentTarget.value = "";
                    }}
                  />
                </label>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {PRODUCT_IMAGE_HINTS.map((hint) => (
                  <span key={hint} className="rounded-full bg-bark-100/70 px-3 py-1 text-xs font-medium text-bark-700">
                    {hint}
                  </span>
                ))}
              </div>
              {productForm.image_url ? (
                <div className="mt-4 rounded-[1.1rem] border border-white/70 bg-[#fff7e5] p-3">
                  <img
                    src={resolveMediaUrl(productForm.image_url)}
                    alt="Предпросмотр товара"
                    className="h-36 w-full rounded-[1rem] object-cover"
                  />
                  <div className="mt-3 flex items-center justify-between gap-3">
                    <p className="min-w-0 truncate text-xs text-fog">{productForm.image_url}</p>
                    <button
                      type="button"
                      onClick={() => setProductForm((current) => ({ ...current, image_url: "" }))}
                      className="pressable rounded-full border border-tea-900/10 px-3 py-2 text-xs font-semibold text-tea-900"
                    >
                      Убрать
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <input value={productForm.name} onChange={(event) => setProductForm((current) => ({ ...current, name: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Название товара" />
            <input value={productForm.slug} onChange={(event) => setProductForm((current) => ({ ...current, slug: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="slug товара" />
          </div>

          <textarea value={productForm.short_description} onChange={(event) => setProductForm((current) => ({ ...current, short_description: event.target.value }))} rows={3} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Короткое описание" />
          <textarea value={productForm.full_description} onChange={(event) => setProductForm((current) => ({ ...current, full_description: event.target.value }))} rows={5} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Полное описание" />

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="flex items-center gap-3 rounded-[1.2rem] bg-white/70 px-4 py-3 text-sm text-tea-900"><input type="checkbox" checked={productForm.is_active} onChange={(event) => setProductForm((current) => ({ ...current, is_active: event.target.checked }))} />Товар активен</label>
            <label className="flex items-center gap-3 rounded-[1.2rem] bg-white/70 px-4 py-3 text-sm text-tea-900"><input type="checkbox" checked={productForm.is_featured} onChange={(event) => setProductForm((current) => ({ ...current, is_featured: event.target.checked }))} />Показывать в популярных</label>
          </div>

          <div className="rounded-[1.35rem] bg-white/60 p-4">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <p className="font-semibold text-tea-900">Фасовки и цены</p>
                <p className="mt-1 text-xs text-fog">Каждая фасовка может иметь свою цену и остаток.</p>
              </div>
              <button type="button" onClick={addPack} className="pressable rounded-full border border-tea-900/10 px-4 py-2 text-sm font-semibold text-tea-900">Добавить фасовку</button>
            </div>

            <div className="space-y-3">
              {productForm.pack_sizes.map((pack, index) => (
                <div key={`${pack.label}-${index}`} className="rounded-[1.2rem] border border-white/70 bg-white p-4">
                  <div className="mb-3 flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-tea-900">Фасовка {index + 1}</p>
                    <div className="flex gap-2">
                      <button type="button" onClick={() => updatePack(index, { is_default: true })} className={`pressable rounded-full px-3 py-2 text-xs font-semibold ${pack.is_default ? "bg-tea-900 text-white" : "border border-tea-900/10 text-tea-900"}`}>По умолчанию</button>
                      <button type="button" onClick={() => removePack(index)} className="pressable rounded-full border border-red-200 px-3 py-2 text-xs font-semibold text-red-500">Удалить</button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <input value={pack.label} onChange={(event) => updatePack(index, { label: event.target.value })} className="rounded-[1.1rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="100 г" />
                    <input type="number" value={pack.weight_grams} onChange={(event) => updatePack(index, { weight_grams: event.target.value })} className="rounded-[1.1rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Вес в граммах" />
                  </div>
                  <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <input type="number" value={pack.price} onChange={(event) => updatePack(index, { price: event.target.value })} className="rounded-[1.1rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Цена, сум" />
                    <input type="number" value={pack.old_price} onChange={(event) => updatePack(index, { old_price: event.target.value })} className="rounded-[1.1rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Старая цена" />
                  </div>
                  <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <input type="number" value={pack.stock_qty} onChange={(event) => updatePack(index, { stock_qty: event.target.value })} className="rounded-[1.1rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Остаток" />
                    <input type="number" value={pack.sort_order} onChange={(event) => updatePack(index, { sort_order: event.target.value })} className="rounded-[1.1rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Порядок" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button type="button" disabled={submitting} onClick={() => void runAction(submitProductForm)} className="pressable flex-1 rounded-full bg-tea-900 px-5 py-4 text-sm font-semibold text-white">{editingProductId ? "Сохранить товар" : "Создать товар"}</button>
            <button type="button" disabled={submitting} onClick={resetProductForm} className="pressable rounded-full border border-tea-900/10 px-5 py-4 text-sm font-semibold text-tea-900">Очистить</button>
          </div>
        </div>
      </section>

      <section className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-tea-900">Управление товарами</h3>
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-fog">{products.length} позиций</span>
        </div>
        <div className="space-y-3">
          {products.map((product) => (
            <div key={product.id} className="rounded-[1.35rem] bg-white/70 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-bold text-tea-900">{product.name}</p>
                  <p className="mt-1 text-sm text-fog">{product.category_name} • {product.default_pack_size.label} • {formatPrice(product.price)}</p>
                  <p className="mt-1 text-xs text-fog">Фасовок: {product.pack_sizes.length} • Остаток: {product.stock_qty} • {product.is_featured ? "Популярный" : "Обычный"}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => { setEditingProductId(product.id); setProductForm(productToForm(product)); setStatusMessage(`Редактируется товар #${product.id}.`); }} className="pressable rounded-full border border-tea-900/10 px-4 py-2 text-sm font-semibold text-tea-900">Редактировать</button>
                  <button type="button" disabled={submitting} onClick={() => void runAction(async () => { const response = await api.toggleAdminProduct(product.id); setStatusMessage(response.message); })} className="pressable rounded-full border border-tea-900/10 px-4 py-2 text-sm font-semibold text-tea-900">{product.is_active ? "Отключить" : "Включить"}</button>
                  <button type="button" disabled={submitting} onClick={() => void runAction(async () => { const post = await api.publishAdminProduct(product.id); setStatusMessage(`Товар опубликован в канал, message_id=${post.message_id ?? "новый пост"}.`); })} className="pressable rounded-full bg-tea-900 px-4 py-2 text-sm font-semibold text-white">В канал</button>
                  <button
                    type="button"
                    disabled={submitting}
                    onClick={() => {
                      if (!window.confirm(`Удалить товар "${product.name}" безвозвратно?`)) return;
                      void runAction(async () => {
                        const response = await api.deleteAdminProduct(product.id);
                        if (editingProductId === product.id) {
                          resetProductForm();
                        }
                        setStatusMessage(response.message);
                      });
                    }}
                    className="pressable inline-flex items-center rounded-full bg-gradient-to-b from-[#B23A2E] to-[#7E231B] px-4 py-2 text-sm font-semibold text-white shadow-soft disabled:opacity-50"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Удалить
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="glass-card p-5">
        <h3 className="text-lg font-bold text-tea-900">Создать акцию</h3>
        <div className="mt-4 grid grid-cols-1 gap-3">
          <input value={promotionForm.title} onChange={(event) => setPromotionForm((current) => ({ ...current, title: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Название акции" />
          <input value={promotionForm.slug} onChange={(event) => setPromotionForm((current) => ({ ...current, slug: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="slug, например spring-tea-season" />
          <textarea value={promotionForm.description} onChange={(event) => setPromotionForm((current) => ({ ...current, description: event.target.value }))} rows={3} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Описание акции" />
          <div className="grid grid-cols-2 gap-3">
            <select value={promotionForm.discount_type} onChange={(event) => setPromotionForm((current) => ({ ...current, discount_type: event.target.value as "percent" | "fixed" }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none">
              <option value="percent">Скидка в процентах</option>
              <option value="fixed">Фиксированная скидка</option>
            </select>
            <input value={promotionForm.discount_value} onChange={(event) => setPromotionForm((current) => ({ ...current, discount_value: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Значение скидки" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input value={promotionForm.badge_text} onChange={(event) => setPromotionForm((current) => ({ ...current, badge_text: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Бейдж" />
            <input value={promotionForm.image_url} onChange={(event) => setPromotionForm((current) => ({ ...current, image_url: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Изображение для поста" />
          </div>
          <label className="flex items-center gap-3 rounded-[1.2rem] bg-white/70 px-4 py-3 text-sm text-tea-900"><input type="checkbox" checked={promotionForm.is_sitewide} onChange={(event) => setPromotionForm((current) => ({ ...current, is_sitewide: event.target.checked }))} />Действует на весь каталог</label>
          <input value={promotionForm.product_ids} onChange={(event) => setPromotionForm((current) => ({ ...current, product_ids: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="ID товаров через запятую" />
          <button type="button" disabled={submitting} onClick={() => void runAction(async () => { await api.createAdminPromotion({ ...promotionForm, image_url: promotionForm.image_url || null, badge_text: promotionForm.badge_text || null, product_ids: parseIds(promotionForm.product_ids), is_active: true }); setPromotionForm(promotionInitialState); setStatusMessage("Акция создана."); })} className="pressable rounded-full bg-tea-900 px-5 py-4 text-sm font-semibold text-white">Создать акцию</button>
        </div>
      </section>

      <section className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-tea-900">Акции</h3>
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-fog">{promotions.length} шт.</span>
        </div>
        <div className="space-y-3">
          {promotions.map((promotion) => (
            <div key={promotion.id} className="rounded-[1.35rem] bg-white/70 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-bold text-tea-900">{promotion.title}</p>
                  <p className="mt-1 text-sm text-fog">{promotion.discount_type === "percent" ? `${promotion.discount_value}%` : formatPrice(promotion.discount_value)} • {promotion.is_sitewide ? "весь каталог" : `товары: ${promotion.product_ids.join(", ") || "—"}`}</p>
                </div>
                <div className="flex gap-2">
                  <button type="button" disabled={submitting} onClick={() => void runAction(async () => { const response = await api.toggleAdminPromotion(promotion.id); setStatusMessage(response.message); })} className="pressable rounded-full border border-tea-900/10 px-4 py-2 text-sm font-semibold text-tea-900">{promotion.is_active ? "Выключить" : "Включить"}</button>
                  <button type="button" disabled={submitting} onClick={() => void runAction(async () => { const post = await api.publishAdminPromotion(promotion.id); setStatusMessage(`Акция опубликована в канал, message_id=${post.message_id ?? "новый пост"}.`); })} className="pressable rounded-full bg-tea-900 px-4 py-2 text-sm font-semibold text-white">В канал</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-tea-900">{editingPromoCodeId ? "Редактирование промокода" : "Создать промокод"}</h3>
            <p className="mt-1 text-sm text-fog">Промокод можно привязать ко всему каталогу или только к отдельным товарам.</p>
          </div>
          {editingPromoCodeId ? <button type="button" onClick={resetPromoCodeForm} className="pressable rounded-full border border-tea-900/10 px-4 py-2 text-sm font-semibold text-tea-900">Новый код</button> : null}
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3">
          <div className="grid grid-cols-2 gap-3">
            <input value={promoCodeForm.code} onChange={(event) => setPromoCodeForm((current) => ({ ...current, code: event.target.value.toUpperCase() }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="TEA10" />
            <input value={promoCodeForm.title} onChange={(event) => setPromoCodeForm((current) => ({ ...current, title: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Название промокода" />
          </div>
          <textarea value={promoCodeForm.description} onChange={(event) => setPromoCodeForm((current) => ({ ...current, description: event.target.value }))} rows={3} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Описание промокода" />
          <div className="grid grid-cols-2 gap-3">
            <select value={promoCodeForm.discount_type} onChange={(event) => setPromoCodeForm((current) => ({ ...current, discount_type: event.target.value as "percent" | "fixed" }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none">
              <option value="percent">Скидка в процентах</option>
              <option value="fixed">Фиксированная скидка</option>
            </select>
            <input value={promoCodeForm.discount_value} onChange={(event) => setPromoCodeForm((current) => ({ ...current, discount_value: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Значение скидки" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input value={promoCodeForm.minimum_order_amount} onChange={(event) => setPromoCodeForm((current) => ({ ...current, minimum_order_amount: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Минимальная сумма заказа" />
            <input value={promoCodeForm.max_uses} onChange={(event) => setPromoCodeForm((current) => ({ ...current, max_uses: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="Лимит использований" />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="flex items-center gap-3 rounded-[1.2rem] bg-white/70 px-4 py-3 text-sm text-tea-900"><input type="checkbox" checked={promoCodeForm.is_sitewide} onChange={(event) => setPromoCodeForm((current) => ({ ...current, is_sitewide: event.target.checked }))} />Действует на весь каталог</label>
            <label className="flex items-center gap-3 rounded-[1.2rem] bg-white/70 px-4 py-3 text-sm text-tea-900"><input type="checkbox" checked={promoCodeForm.is_active} onChange={(event) => setPromoCodeForm((current) => ({ ...current, is_active: event.target.checked }))} />Промокод активен</label>
          </div>
          <input value={promoCodeForm.product_ids} onChange={(event) => setPromoCodeForm((current) => ({ ...current, product_ids: event.target.value }))} className="rounded-[1.2rem] border border-white/70 bg-white px-4 py-3 outline-none" placeholder="ID товаров через запятую, если промокод не глобальный" />
          <div className="flex gap-3">
            <button type="button" disabled={submitting} onClick={() => void runAction(submitPromoCodeForm)} className="pressable flex-1 rounded-full bg-tea-900 px-5 py-4 text-sm font-semibold text-white">{editingPromoCodeId ? "Сохранить промокод" : "Создать промокод"}</button>
            <button type="button" disabled={submitting} onClick={resetPromoCodeForm} className="pressable rounded-full border border-tea-900/10 px-5 py-4 text-sm font-semibold text-tea-900">Очистить</button>
          </div>
        </div>
      </section>

      <section className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-tea-900">Управление промокодами</h3>
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-fog">{promoCodes.length} шт.</span>
        </div>
        <div className="space-y-3">
          {promoCodes.map((promoCode) => (
            <div key={promoCode.id} className="rounded-[1.35rem] bg-white/70 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-bold text-tea-900">{promoCode.code}</p>
                  <p className="mt-1 text-sm text-fog">{promoCode.discount_type === "percent" ? `${promoCode.discount_value}%` : formatPrice(promoCode.discount_value)} • использован {promoCode.times_used} раз</p>
                  <p className="mt-1 text-xs text-fog">{promoCode.is_sitewide ? "Весь каталог" : `Товары: ${promoCode.product_ids.join(", ") || "—"}`} • минимум {promoCode.minimum_order_amount ? formatPrice(promoCode.minimum_order_amount) : "без порога"}</p>
                </div>
                <div className="flex gap-2">
                  <button type="button" onClick={() => { setEditingPromoCodeId(promoCode.id); setPromoCodeForm(promoCodeToForm(promoCode)); setStatusMessage(`Редактируется промокод ${promoCode.code}.`); }} className="pressable rounded-full border border-tea-900/10 px-4 py-2 text-sm font-semibold text-tea-900">Редактировать</button>
                  <button type="button" disabled={submitting} onClick={() => void runAction(async () => { const response = await api.toggleAdminPromoCode(promoCode.id); setStatusMessage(response.message); })} className="pressable rounded-full border border-tea-900/10 px-4 py-2 text-sm font-semibold text-tea-900">{promoCode.is_active ? "Выключить" : "Включить"}</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-tea-900">Посты канала</h3>
            <p className="mt-1 text-sm text-fog">Кнопки в постах теперь открывают бота через безопасный deep link, а бот уже ведет пользователя в Mini App.</p>
          </div>
          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-fog">{channelPosts.length} шт.</span>
        </div>
        <div className="space-y-3">
          {channelPosts.map((post) => (
            <div key={post.id} className="rounded-[1.35rem] bg-white/70 p-4">
              <p className="font-bold text-tea-900">{post.title}</p>
              <p className="mt-1 text-sm text-fog">{post.source_type} #{post.source_id} • message_id {post.message_id ?? "—"}</p>
              <p className="mt-1 text-xs text-fog">Создан: {formatDateTime(post.created_at)}</p>
              {post.deep_link ? <p className="mt-2 break-all text-xs text-bark-700">{post.deep_link}</p> : null}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
