from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.product import ProductCard, ProductDetail
from app.services.catalog import get_product_by_slug, list_products
from app.services.pricing import get_active_sitewide_promotions, serialize_product

router = APIRouter()


@router.get("", response_model=list[ProductCard])
async def get_products(
    category_slug: str | None = None,
    q: str | None = None,
    sort: Literal["default", "price_asc", "price_desc"] = "default",
    discount_only: bool = False,
    in_stock: bool = False,
    featured_only: bool = False,
    session: AsyncSession = Depends(get_db_session),
):
    return await list_products(
        session,
        category_slug=category_slug,
        q=q,
        sort=sort,
        discount_only=discount_only,
        in_stock=in_stock,
        featured_only=featured_only,
    )


@router.get("/featured", response_model=list[ProductCard])
async def get_featured_products(session: AsyncSession = Depends(get_db_session)):
    return await list_products(session, featured_only=True)


@router.get("/search", response_model=list[ProductCard])
async def search_products(
    q: str = Query(min_length=1),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_products(session, q=q)


@router.get("/{slug}", response_model=ProductDetail)
async def get_product(slug: str, session: AsyncSession = Depends(get_db_session)):
    product = await get_product_by_slug(session, slug)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    sitewide_promotions = await get_active_sitewide_promotions(session)
    return serialize_product(product, sitewide_promotions=sitewide_promotions)
