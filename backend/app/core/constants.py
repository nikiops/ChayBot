from enum import StrEnum


class OrderStatus(StrEnum):
    NEW = "new"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class DeliveryType(StrEnum):
    PICKUP = "pickup"
    CITY_DELIVERY = "city_delivery"


class DiscountType(StrEnum):
    PERCENT = "percent"
    FIXED = "fixed"


class ChannelSourceType(StrEnum):
    PRODUCT = "product"
    PROMOTION = "promotion"


class PaymentTicketStatus(StrEnum):
    NEW = "new"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


DEFAULT_ORDER_SORT = "-created_at"
