from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import DiscountType
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.product_pack_size import ProductPackSize
from app.models.promo_code import PromoCode
from app.models.promotion import Promotion

ZERO = Decimal("0.00")
HUNDRED = Decimal("100")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def is_time_window_active(starts_at: datetime | None, ends_at: datetime | None) -> bool:
    now = datetime.now(timezone.utc)
    starts_at = _normalize_datetime(starts_at)
    ends_at = _normalize_datetime(ends_at)
    if starts_at and starts_at > now:
        return False
    if ends_at and ends_at < now:
        return False
    return True


def is_promotion_active(promotion: Promotion) -> bool:
    return promotion.is_active and is_time_window_active(promotion.starts_at, promotion.ends_at)


def is_promo_code_active(promo_code: PromoCode) -> bool:
    if not promo_code.is_active or not is_time_window_active(promo_code.starts_at, promo_code.ends_at):
        return False
    if promo_code.max_uses is not None and promo_code.times_used >= promo_code.max_uses:
        return False
    return True


def calculate_discounted_price(amount: Decimal, discount_type: str, discount_value: Decimal) -> Decimal:
    if discount_type == DiscountType.PERCENT.value:
        next_amount = amount * (HUNDRED - discount_value) / HUNDRED
    else:
        next_amount = amount - discount_value
    return max(_quantize(next_amount), ZERO)


def calculate_discount_amount(amount: Decimal, discount_type: str, discount_value: Decimal) -> Decimal:
    return max(_quantize(amount - calculate_discounted_price(amount, discount_type, discount_value)), ZERO)


def calculate_discount_percent(old_price: Decimal | None, price: Decimal) -> int | None:
    if old_price is None or old_price <= price:
        return None
    return int(((old_price - price) / old_price) * 100)


async def get_active_sitewide_promotions(session: AsyncSession) -> list[Promotion]:
    result = await session.execute(
        select(Promotion)
        .where(Promotion.is_active.is_(True), Promotion.is_sitewide.is_(True))
        .order_by(Promotion.created_at.desc())
    )
    return [promotion for promotion in result.scalars().all() if is_promotion_active(promotion)]


async def get_promo_code_by_code(session: AsyncSession, code: str) -> PromoCode | None:
    normalized = code.strip().upper()
    if not normalized:
        return None
    result = await session.execute(
        select(PromoCode)
        .options(selectinload(PromoCode.products))
        .where(PromoCode.code == normalized)
    )
    promo_code = result.scalar_one_or_none()
    if promo_code is None or not is_promo_code_active(promo_code):
        return None
    return promo_code


def resolve_product_pack_size(product: Product, pack_size_id: int | None = None) -> ProductPackSize | None:
    if pack_size_id is not None:
        for pack_size in product.pack_sizes:
            if pack_size.id == pack_size_id:
                return pack_size
    return product.default_pack_size


def _iter_applicable_promotions(product: Product, sitewide_promotions: Iterable[Promotion]) -> list[Promotion]:
    result: list[Promotion] = []
    seen: set[int] = set()

    for promotion in sitewide_promotions:
        if promotion.id in seen or not is_promotion_active(promotion):
            continue
        result.append(promotion)
        seen.add(promotion.id)

    for promotion in product.promotions:
        if promotion.id in seen or not is_promotion_active(promotion):
            continue
        result.append(promotion)
        seen.add(promotion.id)

    return result


def build_pack_snapshot(
    product: Product,
    pack_size: ProductPackSize | None,
    *,
    sitewide_promotions: Iterable[Promotion] = (),
) -> dict:
    base_label = pack_size.label if pack_size else "Базовая фасовка"
    base_price = pack_size.price if pack_size else product.price
    compare_at_price = pack_size.old_price if pack_size else product.old_price
    stock_qty = pack_size.stock_qty if pack_size else product.stock_qty
    weight_grams = pack_size.weight_grams if pack_size else None
    pack_id = pack_size.id if pack_size else None
    sort_order = pack_size.sort_order if pack_size else 0
    is_default = pack_size.is_default if pack_size else True

    best_price = base_price
    applied_promotion: Promotion | None = None
    for promotion in _iter_applicable_promotions(product, sitewide_promotions):
        candidate = calculate_discounted_price(base_price, promotion.discount_type, promotion.discount_value)
        if candidate < best_price:
            best_price = candidate
            applied_promotion = promotion

    effective_old_price = compare_at_price
    if best_price < base_price:
        effective_old_price = compare_at_price if compare_at_price and compare_at_price > best_price else base_price
    elif compare_at_price is not None and compare_at_price <= best_price:
        effective_old_price = None

    return {
        "id": pack_id,
        "label": base_label,
        "weight_grams": weight_grams,
        "price": _quantize(best_price),
        "old_price": _quantize(effective_old_price) if effective_old_price is not None else None,
        "base_price": _quantize(base_price),
        "stock_qty": stock_qty,
        "sort_order": sort_order,
        "is_default": is_default,
        "is_in_stock": stock_qty > 0,
        "discount_percent": calculate_discount_percent(effective_old_price, best_price),
        "promotion_badge": applied_promotion.badge_text if applied_promotion else None,
        "promotion_title": applied_promotion.title if applied_promotion else None,
    }


def serialize_product(product: Product, *, sitewide_promotions: Iterable[Promotion] = ()) -> dict:
    pack_sizes = product.pack_sizes or []
    pack_snapshots = [
        build_pack_snapshot(product, pack_size, sitewide_promotions=sitewide_promotions)
        for pack_size in pack_sizes
    ]

    if not pack_snapshots:
        pack_snapshots = [build_pack_snapshot(product, None, sitewide_promotions=sitewide_promotions)]

    default_pack_size = next((item for item in pack_snapshots if item["is_default"]), pack_snapshots[0])

    return {
        "id": product.id,
        "category_id": product.category_id,
        "name": product.name,
        "slug": product.slug,
        "short_description": product.short_description,
        "full_description": product.full_description,
        "price": default_pack_size["price"],
        "old_price": default_pack_size["old_price"],
        "image_url": product.image_url,
        "stock_qty": default_pack_size["stock_qty"],
        "is_active": product.is_active,
        "is_featured": product.is_featured,
        "discount_percent": default_pack_size["discount_percent"],
        "is_in_stock": default_pack_size["is_in_stock"],
        "created_at": product.created_at,
        "category": product.category,
        "pack_sizes": pack_snapshots,
        "default_pack_size": default_pack_size,
    }


def promo_code_applies_to_product(promo_code: PromoCode, product_id: int) -> bool:
    return promo_code.is_sitewide or any(product.id == product_id for product in promo_code.products)


def build_cart_payload(
    items: list[CartItem],
    *,
    sitewide_promotions: Iterable[Promotion] = (),
    promo_code: PromoCode | None = None,
) -> dict:
    resolved_items: list[dict] = []
    subtotal = ZERO
    total_items = 0
    eligible_total = ZERO

    for item in items:
        selected_pack = item.pack_size or resolve_product_pack_size(item.product, item.pack_size_id)
        product_payload = serialize_product(item.product, sitewide_promotions=sitewide_promotions)
        pack_snapshot = build_pack_snapshot(item.product, selected_pack, sitewide_promotions=sitewide_promotions)
        line_total = _quantize(pack_snapshot["price"] * item.qty)

        subtotal += line_total
        total_items += item.qty
        if promo_code and promo_code_applies_to_product(promo_code, item.product_id):
            eligible_total += line_total

        resolved_items.append(
            {
                "id": item.id,
                "qty": item.qty,
                "item_total": line_total,
                "product": product_payload,
                "pack_size": pack_snapshot,
            }
        )

    discount_amount = ZERO
    applied_promo_code = None
    promo_code_title = None
    if promo_code is not None:
        if promo_code.minimum_order_amount is not None and subtotal < promo_code.minimum_order_amount:
            raise ValueError(
                f"Промокод {promo_code.code} действует от суммы {promo_code.minimum_order_amount:.0f} сум."
            )
        if eligible_total <= ZERO:
            raise ValueError("Промокод не применяется к товарам в корзине.")

        discount_amount = calculate_discount_amount(
            eligible_total,
            promo_code.discount_type,
            promo_code.discount_value,
        )
        applied_promo_code = promo_code.code
        promo_code_title = promo_code.title

    total = max(_quantize(subtotal - discount_amount), ZERO)

    return {
        "items": resolved_items,
        "subtotal": _quantize(subtotal),
        "discount_amount": _quantize(discount_amount),
        "total": total,
        "total_items": total_items,
        "promo_code": applied_promo_code,
        "promo_code_title": promo_code_title,
    }
