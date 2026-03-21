from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import ORMBaseModel
from app.schemas.product import ProductPackSizeOut


class AdminStatsOut(BaseModel):
    users_count: int
    orders_count: int
    products_count: int
    active_products_count: int
    promotions_count: int
    promo_codes_count: int
    channel_posts_count: int
    payment_tickets_count: int
    pending_payment_tickets_count: int


class AdminProductPackSizeIn(BaseModel):
    label: str = Field(min_length=2, max_length=50)
    weight_grams: int | None = Field(default=None, ge=1)
    price: Decimal = Field(gt=0)
    old_price: Decimal | None = Field(default=None, gt=0)
    stock_qty: int = Field(default=0, ge=0)
    sort_order: int = Field(default=0, ge=0)
    is_default: bool = False


class AdminProductBase(BaseModel):
    category_id: int = Field(ge=1)
    name: str = Field(min_length=3, max_length=255)
    slug: str = Field(min_length=3, max_length=255)
    short_description: str = Field(min_length=10, max_length=600)
    full_description: str = Field(min_length=20, max_length=4000)
    image_url: str = Field(min_length=5, max_length=2000)
    is_active: bool = True
    is_featured: bool = False
    pack_sizes: list[AdminProductPackSizeIn] = Field(min_length=1)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("pack_sizes")
    @classmethod
    def validate_pack_sizes(cls, value: list[AdminProductPackSizeIn]) -> list[AdminProductPackSizeIn]:
        if not value:
            raise ValueError("Добавьте хотя бы одну фасовку.")
        default_count = sum(1 for item in value if item.is_default)
        if default_count > 1:
            raise ValueError("У товара может быть только одна фасовка по умолчанию.")
        return value


class AdminProductCreateIn(AdminProductBase):
    pass


class AdminProductUpdateIn(AdminProductBase):
    pass


class AdminProductOut(ORMBaseModel):
    id: int
    category_id: int
    category_name: str
    name: str
    slug: str
    short_description: str
    full_description: str
    image_url: str
    price: Decimal
    stock_qty: int
    is_active: bool
    is_featured: bool
    default_pack_size: ProductPackSizeOut
    pack_sizes: list[ProductPackSizeOut]
    created_at: datetime


class AdminUploadedImageOut(BaseModel):
    image_url: str
    file_name: str
    content_type: str
    size_bytes: int


class AdminOrderOut(ORMBaseModel):
    id: int
    customer_name: str
    customer_phone: str
    total_amount: Decimal
    status: str
    promo_code: str | None
    created_at: datetime


class AdminPromotionBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    slug: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10, max_length=2000)
    image_url: str | None = None
    badge_text: str | None = Field(default=None, max_length=50)
    discount_type: str
    discount_value: Decimal = Field(gt=0)
    is_sitewide: bool = False
    is_active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    product_ids: list[int] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()


class AdminPromotionCreateIn(AdminPromotionBase):
    pass


class AdminPromotionOut(AdminPromotionBase):
    id: int
    created_at: datetime


class AdminPromoCodeBase(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10, max_length=2000)
    discount_type: str
    discount_value: Decimal = Field(gt=0)
    is_sitewide: bool = False
    minimum_order_amount: Decimal | None = Field(default=None, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    is_active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    product_ids: list[int] = Field(default_factory=list)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

class AdminPromoCodeCreateIn(AdminPromoCodeBase):
    @model_validator(mode="after")
    def validate_scope(self) -> "AdminPromoCodeCreateIn":
        if not self.is_sitewide and not self.product_ids:
            raise ValueError("Укажите товары, если промокод не действует на весь каталог.")
        return self


class AdminPromoCodeUpdateIn(AdminPromoCodeBase):
    @model_validator(mode="after")
    def validate_scope(self) -> "AdminPromoCodeUpdateIn":
        if not self.is_sitewide and not self.product_ids:
            raise ValueError("Укажите товары, если промокод не действует на весь каталог.")
        return self


class AdminPromoCodeOut(AdminPromoCodeBase):
    id: int
    times_used: int
    created_at: datetime


class AdminChannelPostOut(ORMBaseModel):
    id: int
    source_type: str
    source_id: int
    channel_chat_id: str
    message_id: int | None
    title: str
    image_url: str | None
    caption: str
    deep_link: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminPaymentTicketOut(ORMBaseModel):
    id: int
    order_id: int
    order_status: str
    customer_name: str
    customer_phone: str
    customer_contact: str
    delivery_type: str
    payment_amount: Decimal
    promo_code: str | None
    screenshot_path: str
    status: str
    admin_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None
    items_summary: list[str]


class AdminPaymentSettingsOut(BaseModel):
    card_number: str
    card_holder: str | None
    instruction: str
    contact_hint: str


class AdminPaymentSettingsIn(BaseModel):
    card_number: str = Field(min_length=8, max_length=64)
    card_holder: str | None = Field(default=None, max_length=255)
    instruction: str = Field(min_length=10, max_length=2000)
    contact_hint: str = Field(min_length=5, max_length=255)
