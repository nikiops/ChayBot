from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.product_pack_size import ProductPackSize


def _available_stock(product: Product, pack_size: ProductPackSize | None) -> int:
    if pack_size is not None:
        return pack_size.stock_qty
    return product.stock_qty


async def list_cart_items(session: AsyncSession, user_id: int) -> list[CartItem]:
    result = await session.execute(
        select(CartItem)
        .options(
            selectinload(CartItem.product).selectinload(Product.category),
            selectinload(CartItem.product).selectinload(Product.pack_sizes),
            selectinload(CartItem.product).selectinload(Product.promotions),
            selectinload(CartItem.pack_size),
        )
        .where(CartItem.user_id == user_id)
        .join(Product, CartItem.product_id == Product.id)
        .where(Product.is_active.is_(True))
        .order_by(CartItem.id.asc())
    )
    return list(result.scalars().unique().all())


async def add_to_cart(
    session: AsyncSession,
    user_id: int,
    product: Product,
    pack_size: ProductPackSize | None,
    qty: int,
) -> None:
    if _available_stock(product, pack_size) < qty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно товара в выбранной фасовке.",
        )

    result = await session.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == product.id,
            CartItem.pack_size_id == (pack_size.id if pack_size else None),
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        item = CartItem(
            user_id=user_id,
            product_id=product.id,
            pack_size_id=pack_size.id if pack_size else None,
            qty=qty,
        )
        session.add(item)
    else:
        next_qty = item.qty + qty
        if _available_stock(product, pack_size) < next_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недостаточно товара в выбранной фасовке.",
            )
        item.qty = next_qty

    await session.commit()


async def update_cart_item(session: AsyncSession, user_id: int, cart_item_id: int, qty: int) -> None:
    result = await session.execute(
        select(CartItem)
        .options(
            selectinload(CartItem.product).selectinload(Product.pack_sizes),
            selectinload(CartItem.pack_size),
        )
        .where(CartItem.user_id == user_id, CartItem.id == cart_item_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Позиция в корзине не найдена.")

    if _available_stock(item.product, item.pack_size) < qty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно товара в выбранной фасовке.",
        )

    item.qty = qty
    await session.commit()


async def remove_from_cart(session: AsyncSession, user_id: int, cart_item_id: int) -> None:
    await session.execute(
        delete(CartItem).where(CartItem.user_id == user_id, CartItem.id == cart_item_id)
    )
    await session.commit()


async def clear_cart(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await session.commit()
