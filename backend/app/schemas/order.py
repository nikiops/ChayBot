from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.constants import DeliveryType
from app.schemas.payment_ticket import PaymentTicketOut


class OrderCreateIn(BaseModel):
    customer_name: str = Field(min_length=2, max_length=255)
    customer_phone: str = Field(min_length=5, max_length=50)
    comment: str | None = Field(default=None, max_length=1000)
    delivery_type: DeliveryType
    promo_code: str | None = Field(default=None, max_length=50)


class OrderItemOut(BaseModel):
    id: int
    product_id: int | None
    pack_size_id: int | None
    product_name: str
    pack_label: str | None
    pack_weight_grams: int | None
    qty: int
    price: Decimal
    item_total: Decimal


class OrderOut(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    comment: str | None
    delivery_type: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    promo_code: str | None
    total_amount: Decimal
    status: str
    created_at: datetime
    items: list[OrderItemOut]
    payment_ticket: PaymentTicketOut | None = None
