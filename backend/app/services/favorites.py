from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.favorite import Favorite
from app.models.product import Product


async def list_favorites(session: AsyncSession, user_id: int) -> list[Favorite]:
    result = await session.execute(
        select(Favorite)
        .options(selectinload(Favorite.product).selectinload(Product.category))
        .where(Favorite.user_id == user_id)
        .join(Product, Favorite.product_id == Product.id)
        .where(Product.is_active.is_(True))
    )
    return list(result.scalars().unique().all())


async def toggle_favorite(session: AsyncSession, user_id: int, product_id: int) -> bool:
    result = await session.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.product_id == product_id)
    )
    favorite = result.scalar_one_or_none()
    if favorite:
        await session.execute(delete(Favorite).where(Favorite.id == favorite.id))
        await session.commit()
        return False

    session.add(Favorite(user_id=user_id, product_id=product_id))
    await session.commit()
    return True

