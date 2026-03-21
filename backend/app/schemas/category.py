from pydantic import BaseModel

from app.schemas.common import ORMBaseModel


class CategoryOut(ORMBaseModel):
    id: int
    name: str
    slug: str
    description: str
    image_url: str
    is_active: bool
    sort_order: int


class CategoryWithCount(CategoryOut):
    product_count: int

