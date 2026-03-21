from app.schemas.common import ORMBaseModel
from app.schemas.product import ProductCard


class FavoriteToggleIn(ORMBaseModel):
    product_id: int


class FavoriteItemOut(ORMBaseModel):
    id: int
    product: ProductCard

