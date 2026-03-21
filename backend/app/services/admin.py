from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.constants import DiscountType
from app.models.cart_item import CartItem
from app.models.category import Category
from app.models.channel_post import ChannelPost
from app.models.favorite import Favorite
from app.models.order import Order
from app.models.order import OrderItem
from app.models.payment_ticket import PaymentTicket
from app.models.product import Product
from app.models.product_pack_size import ProductPackSize
from app.models.promo_code import PromoCode
from app.models.promo_code import promo_code_products
from app.models.promotion import Promotion
from app.models.promotion import promotion_products
from app.models.user import User
from app.services.media import resolve_media_path
from app.services.channel import (
    get_product_for_channel,
    get_promotion_for_channel,
    list_channel_posts,
    publish_product_to_channel,
    publish_promotion_to_channel,
)
from app.services.pricing import get_active_sitewide_promotions, serialize_product


def _ensure_discount_type(discount_type: str) -> None:
    if discount_type not in {DiscountType.PERCENT.value, DiscountType.FIXED.value}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только скидки percent и fixed.",
        )


def _normalize_pack_sizes(pack_sizes) -> list[dict]:
    normalized: list[dict] = []
    has_default = False

    for index, pack_size in enumerate(pack_sizes):
        is_default = bool(pack_size.is_default)
        if is_default:
            has_default = True
        old_price = pack_size.old_price
        if old_price is not None and old_price <= pack_size.price:
            old_price = None
        normalized.append(
            {
                "label": pack_size.label.strip(),
                "weight_grams": pack_size.weight_grams,
                "price": pack_size.price,
                "old_price": old_price,
                "stock_qty": pack_size.stock_qty,
                "sort_order": pack_size.sort_order if pack_size.sort_order is not None else index,
                "is_default": is_default,
            }
        )

    if normalized and not has_default:
        normalized[0]["is_default"] = True

    return sorted(normalized, key=lambda item: (item["sort_order"], item["weight_grams"] or 0, item["label"]))


async def _ensure_category_exists(session: AsyncSession, category_id: int) -> None:
    result = await session.execute(select(Category.id).where(Category.id == category_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена.")


async def _ensure_unique_product_slug(
    session: AsyncSession,
    slug: str,
    *,
    exclude_product_id: int | None = None,
) -> None:
    stmt = select(Product.id).where(Product.slug == slug)
    if exclude_product_id is not None:
        stmt = stmt.where(Product.id != exclude_product_id)
    result = await session.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Товар с таким slug уже существует.",
        )


async def _ensure_unique_promo_code(
    session: AsyncSession,
    code: str,
    *,
    exclude_promo_code_id: int | None = None,
) -> None:
    stmt = select(PromoCode.id).where(PromoCode.code == code)
    if exclude_promo_code_id is not None:
        stmt = stmt.where(PromoCode.id != exclude_promo_code_id)
    result = await session.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Промокод с таким кодом уже существует.",
        )


async def _resolve_products_for_scope(session: AsyncSession, product_ids: list[int]) -> list[Product]:
    unique_ids = list(dict.fromkeys(product_ids))
    if not unique_ids:
        return []

    result = await session.execute(select(Product).where(Product.id.in_(unique_ids)))
    products = list(result.scalars().all())
    found_ids = {product.id for product in products}
    missing_ids = [product_id for product_id in unique_ids if product_id not in found_ids]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Не найдены товары с id: {', '.join(str(item) for item in missing_ids)}.",
        )
    return products


async def _get_product_for_admin(session: AsyncSession, product_id: int) -> Product | None:
    result = await session.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.pack_sizes),
            selectinload(Product.promotions),
        )
        .where(Product.id == product_id)
    )
    return result.scalars().unique().one_or_none()


async def _get_promo_code_for_admin(session: AsyncSession, promo_code_id: int) -> PromoCode | None:
    result = await session.execute(
        select(PromoCode)
        .options(selectinload(PromoCode.products))
        .where(PromoCode.id == promo_code_id)
    )
    return result.scalars().unique().one_or_none()


async def _get_promotion_for_admin(session: AsyncSession, promotion_id: int) -> Promotion | None:
    result = await session.execute(
        select(Promotion)
        .options(selectinload(Promotion.products))
        .where(Promotion.id == promotion_id)
    )
    return result.scalars().unique().one_or_none()


async def _serialize_admin_product(session: AsyncSession, product: Product) -> dict:
    sitewide_promotions = await get_active_sitewide_promotions(session)
    payload = serialize_product(product, sitewide_promotions=sitewide_promotions)
    payload["category_name"] = product.category.name if product.category else ""
    return payload


def _apply_product_payload(product: Product, payload) -> None:
    normalized_pack_sizes = _normalize_pack_sizes(payload.pack_sizes)
    default_pack = next((item for item in normalized_pack_sizes if item["is_default"]), normalized_pack_sizes[0])

    product.category_id = payload.category_id
    product.name = payload.name.strip()
    product.slug = payload.slug.strip().lower()
    product.short_description = payload.short_description.strip()
    product.full_description = payload.full_description.strip()
    product.image_url = payload.image_url.strip()
    product.is_active = payload.is_active
    product.is_featured = payload.is_featured
    product.price = Decimal(default_pack["price"])
    product.old_price = default_pack["old_price"]
    product.stock_qty = sum(item["stock_qty"] for item in normalized_pack_sizes)
    product.pack_sizes = [ProductPackSize(**pack_size_data) for pack_size_data in normalized_pack_sizes]


async def get_admin_stats(session: AsyncSession) -> dict:
    users_count = await session.scalar(select(func.count(User.id)))
    orders_count = await session.scalar(select(func.count(Order.id)))
    products_count = await session.scalar(select(func.count(Product.id)))
    active_products_count = await session.scalar(select(func.count(Product.id)).where(Product.is_active.is_(True)))
    promotions_count = await session.scalar(select(func.count(Promotion.id)))
    promo_codes_count = await session.scalar(select(func.count(PromoCode.id)))
    channel_posts_count = await session.scalar(select(func.count(ChannelPost.id)))
    payment_tickets_count = await session.scalar(select(func.count(PaymentTicket.id)))
    pending_payment_tickets_count = await session.scalar(
        select(func.count(PaymentTicket.id)).where(PaymentTicket.status == "new")
    )
    return {
        "users_count": users_count or 0,
        "orders_count": orders_count or 0,
        "products_count": products_count or 0,
        "active_products_count": active_products_count or 0,
        "promotions_count": promotions_count or 0,
        "promo_codes_count": promo_codes_count or 0,
        "channel_posts_count": channel_posts_count or 0,
        "payment_tickets_count": payment_tickets_count or 0,
        "pending_payment_tickets_count": pending_payment_tickets_count or 0,
    }


async def list_admin_orders(session: AsyncSession, limit: int = 10) -> list[Order]:
    result = await session.execute(select(Order).order_by(Order.created_at.desc()).limit(limit))
    return list(result.scalars().all())


async def list_admin_products(session: AsyncSession, limit: int = 100) -> list[dict]:
    result = await session.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.pack_sizes),
            selectinload(Product.promotions),
        )
        .order_by(Product.created_at.desc())
        .limit(limit)
    )
    sitewide_promotions = await get_active_sitewide_promotions(session)
    products = result.scalars().unique().all()
    payload: list[dict] = []
    for product in products:
        item = serialize_product(product, sitewide_promotions=sitewide_promotions)
        item["category_name"] = product.category.name if product.category else ""
        payload.append(item)
    return payload


async def create_admin_product(session: AsyncSession, payload) -> dict:
    await _ensure_category_exists(session, payload.category_id)
    await _ensure_unique_product_slug(session, payload.slug)

    product = Product(
        category_id=payload.category_id,
        name=payload.name.strip(),
        slug=payload.slug.strip().lower(),
        short_description=payload.short_description.strip(),
        full_description=payload.full_description.strip(),
        price=Decimal("0"),
        old_price=None,
        image_url=payload.image_url.strip(),
        stock_qty=0,
        is_active=payload.is_active,
        is_featured=payload.is_featured,
    )
    _apply_product_payload(product, payload)

    session.add(product)
    await session.commit()

    created_product = await _get_product_for_admin(session, product.id)
    if created_product is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось загрузить товар после создания.")
    return await _serialize_admin_product(session, created_product)


async def update_admin_product(session: AsyncSession, product_id: int, payload) -> dict | None:
    product = await _get_product_for_admin(session, product_id)
    if product is None:
        return None

    await _ensure_category_exists(session, payload.category_id)
    await _ensure_unique_product_slug(session, payload.slug, exclude_product_id=product_id)
    _apply_product_payload(product, payload)
    await session.commit()

    updated_product = await _get_product_for_admin(session, product_id)
    if updated_product is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось загрузить товар после обновления.")
    return await _serialize_admin_product(session, updated_product)


async def toggle_product_active(session: AsyncSession, product_id: int) -> Product | None:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        return None
    product.is_active = not product.is_active
    await session.commit()
    await session.refresh(product)
    return product


async def delete_admin_product(session: AsyncSession, settings: Settings, product_id: int) -> str | None:
    product = await _get_product_for_admin(session, product_id)
    if product is None:
        return None

    product_name = product.name
    image_path = resolve_media_path(settings, product.image_url)
    pack_size_ids = [pack_size.id for pack_size in product.pack_sizes if pack_size.id is not None]

    await session.execute(
        update(OrderItem)
        .where(OrderItem.product_id == product_id)
        .values(product_id=None)
    )
    if pack_size_ids:
        await session.execute(
            update(OrderItem)
            .where(OrderItem.pack_size_id.in_(pack_size_ids))
            .values(pack_size_id=None)
        )

    await session.execute(delete(Favorite).where(Favorite.product_id == product_id))
    await session.execute(delete(CartItem).where(CartItem.product_id == product_id))
    await session.execute(delete(promotion_products).where(promotion_products.c.product_id == product_id))
    await session.execute(delete(promo_code_products).where(promo_code_products.c.product_id == product_id))
    await session.execute(
        delete(ChannelPost).where(
            ChannelPost.source_type == "product",
            ChannelPost.source_id == product_id,
        )
    )
    await session.execute(delete(ProductPackSize).where(ProductPackSize.product_id == product_id))
    await session.execute(delete(Product).where(Product.id == product_id))
    await session.commit()

    if image_path is not None:
        image_path.unlink(missing_ok=True)

    return product_name


async def list_promotions(session: AsyncSession, limit: int = 100) -> list[Promotion]:
    result = await session.execute(
        select(Promotion)
        .options(selectinload(Promotion.products))
        .order_by(Promotion.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().unique().all())


async def create_promotion(session: AsyncSession, payload) -> Promotion:
    _ensure_discount_type(payload.discount_type)

    promotion = Promotion(
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        image_url=payload.image_url,
        badge_text=payload.badge_text,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        is_sitewide=payload.is_sitewide,
        is_active=payload.is_active,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )

    if payload.product_ids:
        promotion.products = await _resolve_products_for_scope(session, payload.product_ids)

    session.add(promotion)
    await session.commit()
    refreshed = await _get_promotion_for_admin(session, promotion.id)
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось загрузить акцию после создания.")
    return refreshed


async def toggle_promotion_active(session: AsyncSession, promotion_id: int) -> Promotion | None:
    result = await session.execute(select(Promotion).where(Promotion.id == promotion_id))
    promotion = result.scalar_one_or_none()
    if promotion is None:
        return None
    promotion.is_active = not promotion.is_active
    await session.commit()
    await session.refresh(promotion)
    return promotion


async def list_promo_codes(session: AsyncSession, limit: int = 100) -> list[PromoCode]:
    result = await session.execute(
        select(PromoCode)
        .options(selectinload(PromoCode.products))
        .order_by(PromoCode.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().unique().all())


async def create_promo_code(session: AsyncSession, payload) -> PromoCode:
    _ensure_discount_type(payload.discount_type)
    await _ensure_unique_promo_code(session, payload.code)

    promo_code = PromoCode(
        code=payload.code.strip().upper(),
        title=payload.title,
        description=payload.description,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        is_sitewide=payload.is_sitewide,
        minimum_order_amount=payload.minimum_order_amount,
        max_uses=payload.max_uses,
        is_active=payload.is_active,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
    )

    if payload.product_ids:
        promo_code.products = await _resolve_products_for_scope(session, payload.product_ids)

    session.add(promo_code)
    await session.commit()
    refreshed = await _get_promo_code_for_admin(session, promo_code.id)
    if refreshed is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось загрузить промокод после создания.")
    return refreshed


async def update_promo_code(session: AsyncSession, promo_code_id: int, payload) -> PromoCode | None:
    _ensure_discount_type(payload.discount_type)
    promo_code = await _get_promo_code_for_admin(session, promo_code_id)
    if promo_code is None:
        return None

    await _ensure_unique_promo_code(session, payload.code, exclude_promo_code_id=promo_code_id)
    promo_code.code = payload.code.strip().upper()
    promo_code.title = payload.title
    promo_code.description = payload.description
    promo_code.discount_type = payload.discount_type
    promo_code.discount_value = payload.discount_value
    promo_code.is_sitewide = payload.is_sitewide
    promo_code.minimum_order_amount = payload.minimum_order_amount
    promo_code.max_uses = payload.max_uses
    promo_code.is_active = payload.is_active
    promo_code.starts_at = payload.starts_at
    promo_code.ends_at = payload.ends_at
    promo_code.products = await _resolve_products_for_scope(session, payload.product_ids)

    await session.commit()
    refreshed = await _get_promo_code_for_admin(session, promo_code_id)
    return refreshed


async def toggle_promo_code_active(session: AsyncSession, promo_code_id: int) -> PromoCode | None:
    result = await session.execute(select(PromoCode).where(PromoCode.id == promo_code_id))
    promo_code = result.scalar_one_or_none()
    if promo_code is None:
        return None
    promo_code.is_active = not promo_code.is_active
    await session.commit()
    await session.refresh(promo_code)
    return promo_code


async def list_admin_channel_posts(session: AsyncSession, limit: int = 50) -> list[ChannelPost]:
    return await list_channel_posts(session, limit=limit)


async def publish_product_post(session: AsyncSession, settings: Settings, product_id: int) -> ChannelPost | None:
    product = await get_product_for_channel(session, product_id)
    if product is None:
        return None
    return await publish_product_to_channel(session, settings, product=product)


async def publish_promotion_post(session: AsyncSession, settings: Settings, promotion_id: int) -> ChannelPost | None:
    promotion = await get_promotion_for_channel(session, promotion_id)
    if promotion is None:
        return None
    return await publish_promotion_to_channel(session, settings, promotion=promotion)
