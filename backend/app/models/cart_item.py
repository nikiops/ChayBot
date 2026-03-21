from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", "pack_size_id", name="uq_cart_items_user_product_pack"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    pack_size_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_pack_sizes.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    pack_size = relationship("ProductPackSize", back_populates="cart_items")
