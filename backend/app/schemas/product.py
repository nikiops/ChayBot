from datetime import datetime
from decimal import Decimal

from app.schemas.category import CategoryOut
from app.schemas.common import ORMBaseModel


class ProductPackSizeOut(ORMBaseModel):
    id: int | None
    label: str
    weight_grams: int | None
    price: Decimal
    old_price: Decimal | None
    base_price: Decimal
    stock_qty: int
    sort_order: int
    is_default: bool
    is_in_stock: bool
    discount_percent: int | None = None
    promotion_badge: str | None = None
    promotion_title: str | None = None


class ProductCard(ORMBaseModel):
    id: int
    category_id: int
    name: str
    slug: str
    short_description: str
    price: Decimal
    old_price: Decimal | None
    image_url: str
    stock_qty: int
    is_active: bool
    is_featured: bool
    discount_percent: int | None = None
    is_in_stock: bool
    pack_sizes: list[ProductPackSizeOut]
    default_pack_size: ProductPackSizeOut


class ProductDetail(ProductCard):
    full_description: str
    created_at: datetime
    category: CategoryOut
