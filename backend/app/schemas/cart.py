from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.product import ProductCard, ProductPackSizeOut


class CartMutationIn(BaseModel):
    product_id: int
    pack_size_id: int | None = None
    qty: int = Field(default=1, ge=1, le=99)


class CartUpdateIn(BaseModel):
    cart_item_id: int
    qty: int = Field(default=1, ge=1, le=99)


class CartRemoveIn(BaseModel):
    cart_item_id: int


class CartItemOut(BaseModel):
    id: int
    qty: int
    item_total: Decimal
    product: ProductCard
    pack_size: ProductPackSizeOut


class CartOut(BaseModel):
    items: list[CartItemOut]
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    total_items: int
    promo_code: str | None = None
    promo_code_title: str | None = None
