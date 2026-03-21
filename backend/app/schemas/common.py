from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ORMBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class PriceSummary(BaseModel):
    subtotal: Decimal
    total: Decimal

