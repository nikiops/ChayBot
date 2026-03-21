from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.core.constants import DeliveryType
from app.schemas.common import ORMBaseModel


class CheckoutPaymentConfigOut(BaseModel):
    card_number: str
    card_holder: str | None
    instruction: str
    contact_hint: str


class PaymentTicketCheckoutIn(BaseModel):
    customer_name: str = Field(min_length=2, max_length=255)
    customer_phone: str = Field(min_length=5, max_length=50)
    customer_contact: str = Field(max_length=255)
    comment: str | None = Field(default=None, max_length=1000)
    delivery_type: DeliveryType
    promo_code: str | None = Field(default=None, max_length=50)

    @field_validator("customer_name", "customer_phone", "customer_contact", mode="before")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @field_validator("customer_contact")
    @classmethod
    def validate_customer_contact(cls, value: str) -> str:
        compact_value = value.replace(" ", "")
        if len(compact_value) < 3 or compact_value in {"+", "@"}:
            raise ValueError("Укажите телефон или @telegram для связи по оплате.")
        return value


class PaymentTicketOut(ORMBaseModel):
    id: int
    customer_contact: str
    payment_amount: Decimal
    payment_card_number: str
    payment_card_holder: str | None
    instructions: str | None
    screenshot_path: str
    status: str
    admin_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None
