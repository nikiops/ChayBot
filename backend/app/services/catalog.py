from typing import Literal

from sqlalchemy import Select, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.product import Product
from app.services.pricing import get_active_sitewide_promotions, serialize_product

ProductSort = Literal["default", "price_asc", "price_desc"]


async def list_categories(session: AsyncSession) -> list[dict]:
    stmt = (
        select(
            Category.id,
            Category.name,
            Category.slug,
            Category.description,
            Category.image_url,
            Category.is_active,
            Category.sort_order,
            func.count(Product.id).label("product_count"),
        )
        .outerjoin(Product, Product.category_id == Category.id)
        .where(Category.is_active.is_(True))
        .group_by(Category.id)
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )
    result = await session.execute(stmt)
    return [dict(row._mapping) for row in result.all()]


async def get_category_by_slug(session: AsyncSession, slug: str) -> Category | None:
    result = await session.execute(
        select(Category).where(Category.slug == slug, Category.is_active.is_(True))
    )
    return result.scalar_one_or_none()


def _products_base_query() -> Select[tuple[Product]]:
    return (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.pack_sizes),
            selectinload(Product.promotions),
        )
        .join(Category, Category.id == Product.category_id)
        .where(Product.is_active.is_(True), Category.is_active.is_(True))
    )


async def list_products(
    session: AsyncSession,
    *,
    category_slug: str | None = None,
    q: str | None = None,
    sort: ProductSort = "default",
    discount_only: bool = False,
    in_stock: bool = False,
    featured_only: bool = False,
) -> list[dict]:
    stmt = _products_base_query()

    if category_slug:
        stmt = stmt.where(Category.slug == category_slug)
    if q:
        search = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(search),
                Product.short_description.ilike(search),
                Product.full_description.ilike(search),
            )
        )
    if featured_only:
        stmt = stmt.where(Product.is_featured.is_(True))

    stmt = stmt.order_by(desc(Product.is_featured), desc(Product.created_at))

    sitewide_promotions = await get_active_sitewide_promotions(session)
    result = await session.execute(stmt)
    products = [serialize_product(product, sitewide_promotions=sitewide_promotions) for product in result.scalars().unique().all()]

    if discount_only:
        products = [product for product in products if product["old_price"] and product["old_price"] > product["price"]]
    if in_stock:
        products = [product for product in products if product["is_in_stock"]]

    if sort == "price_asc":
        products.sort(key=lambda product: (product["price"], product["name"]))
    elif sort == "price_desc":
        products.sort(key=lambda product: (product["price"], product["name"]), reverse=True)
    else:
        products.sort(key=lambda product: (not product["is_featured"], -product["created_at"].timestamp()))

    return products


async def get_product_by_slug(session: AsyncSession, slug: str) -> Product | None:
    result = await session.execute(_products_base_query().where(Product.slug == slug))
    return result.scalars().unique().one_or_none()


async def get_product_by_id(session: AsyncSession, product_id: int) -> Product | None:
    result = await session.execute(_products_base_query().where(Product.id == product_id))
    return result.scalars().unique().one_or_none()
