from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    short_description: Mapped[str] = mapped_column(Text)
    full_description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    image_url: Mapped[str] = mapped_column(Text)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    category = relationship("Category", back_populates="products")
    favorites = relationship("Favorite", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    pack_sizes = relationship(
        "ProductPackSize",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductPackSize.sort_order.asc()",
    )
    promotions = relationship("Promotion", secondary="promotion_products", back_populates="products")
    promo_codes = relationship("PromoCode", secondary="promo_code_products", back_populates="products")

    @property
    def default_pack_size(self):
        for pack_size in self.pack_sizes:
            if pack_size.is_default:
                return pack_size
        return self.pack_sizes[0] if self.pack_sizes else None

    @property
    def discount_percent(self) -> int | None:
        pack_size = self.default_pack_size
        if pack_size is not None:
            return pack_size.discount_percent
        if not self.old_price or self.old_price <= self.price:
            return None
        return int(((self.old_price - self.price) / self.old_price) * 100)

    @property
    def is_in_stock(self) -> bool:
        pack_size = self.default_pack_size
        if pack_size is not None:
            return pack_size.is_in_stock
        return self.stock_qty > 0
