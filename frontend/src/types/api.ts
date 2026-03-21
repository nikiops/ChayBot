export type Category = {
  id: number;
  name: string;
  slug: string;
  description: string;
  image_url: string;
  is_active: boolean;
  sort_order: number;
  product_count?: number;
};

export type ProductPackSize = {
  id: number | null;
  label: string;
  weight_grams: number | null;
  price: string;
  old_price: string | null;
  base_price: string;
  stock_qty: number;
  sort_order: number;
  is_default: boolean;
  is_in_stock: boolean;
  discount_percent: number | null;
  promotion_badge: string | null;
  promotion_title: string | null;
};

export type Product = {
  id: number;
  category_id: number;
  name: string;
  slug: string;
  short_description: string;
  full_description?: string;
  price: string;
  old_price: string | null;
  image_url: string;
  stock_qty: number;
  is_active: boolean;
  is_featured: boolean;
  discount_percent: number | null;
  is_in_stock: boolean;
  created_at?: string;
  category?: Category;
  pack_sizes: ProductPackSize[];
  default_pack_size: ProductPackSize;
};

export type Favorite = {
  id: number;
  product: Product;
};

export type CartItem = {
  id: number;
  qty: number;
  item_total: string;
  product: Product;
  pack_size: ProductPackSize;
};

export type Cart = {
  items: CartItem[];
  subtotal: string;
  discount_amount: string;
  total: string;
  total_items: number;
  promo_code: string | null;
  promo_code_title: string | null;
};

export type DeliveryType = "pickup" | "city_delivery";

export type OrderItem = {
  id: number;
  product_id: number | null;
  pack_size_id: number | null;
  product_name: string;
  pack_label: string | null;
  pack_weight_grams: number | null;
  qty: number;
  price: string;
  item_total: string;
};

export type Order = {
  id: number;
  customer_name: string;
  customer_phone: string;
  comment: string | null;
  delivery_type: DeliveryType;
  subtotal_amount: string;
  discount_amount: string;
  promo_code: string | null;
  total_amount: string;
  status: string;
  created_at: string;
  items: OrderItem[];
  payment_ticket: PaymentTicket | null;
};

export type AdminStats = {
  users_count: number;
  orders_count: number;
  products_count: number;
  active_products_count: number;
  promotions_count: number;
  promo_codes_count: number;
  channel_posts_count: number;
  payment_tickets_count: number;
  pending_payment_tickets_count: number;
};

export type AdminProduct = {
  id: number;
  category_id: number;
  category_name: string;
  name: string;
  slug: string;
  short_description: string;
  full_description: string;
  image_url: string;
  price: string;
  stock_qty: number;
  is_active: boolean;
  is_featured: boolean;
  default_pack_size: ProductPackSize;
  pack_sizes: ProductPackSize[];
  created_at: string;
};

export type AdminProductPackSizeInput = {
  label: string;
  weight_grams: number | null;
  price: string;
  old_price: string | null;
  stock_qty: number;
  sort_order: number;
  is_default: boolean;
};

export type AdminProductPayload = {
  category_id: number;
  name: string;
  slug: string;
  short_description: string;
  full_description: string;
  image_url: string;
  is_active: boolean;
  is_featured: boolean;
  pack_sizes: AdminProductPackSizeInput[];
};

export type AdminUploadedImage = {
  image_url: string;
  file_name: string;
  content_type: string;
  size_bytes: number;
};

export type AdminPromotion = {
  id: number;
  title: string;
  slug: string;
  description: string;
  image_url: string | null;
  badge_text: string | null;
  discount_type: "percent" | "fixed";
  discount_value: string;
  is_sitewide: boolean;
  is_active: boolean;
  starts_at: string | null;
  ends_at: string | null;
  product_ids: number[];
  created_at: string;
};

export type AdminPromoCode = {
  id: number;
  code: string;
  title: string;
  description: string;
  discount_type: "percent" | "fixed";
  discount_value: string;
  is_sitewide: boolean;
  minimum_order_amount: string | null;
  max_uses: number | null;
  is_active: boolean;
  starts_at: string | null;
  ends_at: string | null;
  product_ids: number[];
  times_used: number;
  created_at: string;
};

export type AdminPromoCodePayload = {
  code: string;
  title: string;
  description: string;
  discount_type: "percent" | "fixed";
  discount_value: string;
  is_sitewide: boolean;
  minimum_order_amount: string | null;
  max_uses: number | null;
  is_active: boolean;
  product_ids: number[];
};

export type AdminChannelPost = {
  id: number;
  source_type: "product" | "promotion";
  source_id: number;
  channel_chat_id: string;
  message_id: number | null;
  title: string;
  image_url: string | null;
  caption: string;
  deep_link: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type PaymentTicket = {
  id: number;
  customer_contact: string;
  payment_amount: string;
  payment_card_number: string;
  payment_card_holder: string | null;
  instructions: string | null;
  screenshot_path: string;
  status: string;
  admin_comment: string | null;
  created_at: string;
  reviewed_at: string | null;
};

export type CheckoutPaymentConfig = {
  card_number: string;
  card_holder: string | null;
  instruction: string;
  contact_hint: string;
};

export type AdminPaymentTicket = {
  id: number;
  order_id: number;
  order_status: string;
  customer_name: string;
  customer_phone: string;
  customer_contact: string;
  delivery_type: DeliveryType;
  payment_amount: string;
  promo_code: string | null;
  screenshot_path: string;
  status: string;
  admin_comment: string | null;
  created_at: string;
  reviewed_at: string | null;
  items_summary: string[];
};

export type AdminPaymentSettings = {
  card_number: string;
  card_holder: string | null;
  instruction: string;
  contact_hint: string;
};
