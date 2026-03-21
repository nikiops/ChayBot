from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.constants import OrderStatus
from app.models.cart_item import CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreateIn
from app.services.pricing import build_cart_payload, get_active_sitewide_promotions, get_promo_code_by_code
from app.services.telegram import send_order_notification


async def load_cart_checkout_context(
    session: AsyncSession,
    user: User,
    *,
    promo_code_value: str | None = None,
) -> tuple[list[CartItem], dict, object | None]:
    result = await session.execute(
        select(CartItem)
        .options(
            selectinload(CartItem.product).selectinload(Product.category),
            selectinload(CartItem.product).selectinload(Product.pack_sizes),
            selectinload(CartItem.product).selectinload(Product.promotions),
            selectinload(CartItem.pack_size),
        )
        .where(CartItem.user_id == user.id)
        .order_by(CartItem.id.asc())
    )
    cart_items = list(result.scalars().all())
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Корзина пуста.")

    sitewide_promotions = await get_active_sitewide_promotions(session)
    promo_code = await get_promo_code_by_code(session, promo_code_value) if promo_code_value else None

    try:
        cart_payload = build_cart_payload(
            cart_items,
            sitewide_promotions=sitewide_promotions,
            promo_code=promo_code,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return cart_items, cart_payload, promo_code


def apply_customer_phone(user: User, phone: str | None) -> None:
    if not user.phone and phone:
        user.phone = phone


def create_order_entity(
    user: User,
    payload: OrderCreateIn,
    cart_payload: dict,
    *,
    status_value: str = OrderStatus.NEW.value,
) -> Order:
    return Order(
        user_id=user.id,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        comment=payload.comment,
        delivery_type=payload.delivery_type.value,
        subtotal_amount=cart_payload["subtotal"],
        discount_amount=cart_payload["discount_amount"],
        promo_code=cart_payload["promo_code"],
        total_amount=cart_payload["total"],
        status=status_value,
    )


async def attach_order_items(
    session: AsyncSession,
    order: Order,
    *,
    cart_items: list[CartItem],
    cart_payload: dict,
) -> None:
    cart_items_by_id = {item.id: item for item in cart_items}
    for item_payload in cart_payload["items"]:
        cart_item = cart_items_by_id[item_payload["id"]]
        pack_size = cart_item.pack_size
        product = cart_item.product
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id if product else None,
                pack_size_id=pack_size.id if pack_size else None,
                pack_label=item_payload["pack_size"]["label"],
                pack_weight_grams=item_payload["pack_size"]["weight_grams"],
                qty=cart_item.qty,
                price=item_payload["pack_size"]["price"],
            )
        )


def reserve_cart_inventory(cart_items: list[CartItem]) -> None:
    for cart_item in cart_items:
        pack_size = cart_item.pack_size
        product = cart_item.product

        if pack_size is not None:
            if pack_size.stock_qty < cart_item.qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Недостаточно фасовки '{pack_size.label}' для товара '{product.name}'.",
                )
            pack_size.stock_qty -= cart_item.qty
            continue

        if product is not None:
            if product.stock_qty < cart_item.qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Недостаточно товара '{product.name}' в наличии.",
                )
            product.stock_qty -= cart_item.qty


async def clear_cart_items(session: AsyncSession, cart_items: list[CartItem]) -> None:
    for cart_item in cart_items:
        await session.delete(cart_item)


async def create_order_from_cart(
    session: AsyncSession,
    user: User,
    payload: OrderCreateIn,
    settings: Settings,
) -> Order:
    cart_items, cart_payload, promo_code = await load_cart_checkout_context(
        session,
        user,
        promo_code_value=payload.promo_code,
    )

    order = create_order_entity(user, payload, cart_payload, status_value=OrderStatus.NEW.value)
    session.add(order)
    await session.flush()

    await attach_order_items(session, order, cart_items=cart_items, cart_payload=cart_payload)
    reserve_cart_inventory(cart_items)

    if promo_code is not None:
        promo_code.times_used += 1

    await clear_cart_items(session, cart_items)
    apply_customer_phone(user, payload.customer_phone)

    await session.commit()

    refreshed_order = await get_order_by_id(session, order.id, user.id)
    if refreshed_order is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Заказ не найден.")

    await send_order_notification(settings, refreshed_order)
    return refreshed_order


async def get_order_by_id(session: AsyncSession, order_id: int, user_id: int | None = None) -> Order | None:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.pack_size),
            selectinload(Order.payment_ticket),
        )
        .where(Order.id == order_id)
    )
    if user_id is not None:
        stmt = stmt.where(Order.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().unique().one_or_none()


def serialize_payment_ticket(ticket) -> dict | None:
    if ticket is None:
        return None
    return {
        "id": ticket.id,
        "customer_contact": ticket.customer_contact,
        "payment_amount": ticket.payment_amount,
        "payment_card_number": ticket.payment_card_number,
        "payment_card_holder": ticket.payment_card_holder,
        "instructions": ticket.instructions,
        "screenshot_path": ticket.screenshot_path,
        "status": ticket.status,
        "admin_comment": ticket.admin_comment,
        "created_at": ticket.created_at,
        "reviewed_at": ticket.reviewed_at,
    }


def serialize_order(order: Order) -> dict:
    items: list[dict] = []
    for item in order.items:
        product_name = item.product.name if item.product else f"Товар #{item.product_id}"
        item_total = (item.price or Decimal("0.00")) * item.qty
        items.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "pack_size_id": item.pack_size_id,
                "product_name": product_name,
                "pack_label": item.pack_label,
                "pack_weight_grams": item.pack_weight_grams,
                "qty": item.qty,
                "price": item.price,
                "item_total": item_total,
            }
        )

    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "comment": order.comment,
        "delivery_type": order.delivery_type,
        "subtotal_amount": order.subtotal_amount,
        "discount_amount": order.discount_amount,
        "promo_code": order.promo_code,
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": order.created_at,
        "items": items,
        "payment_ticket": serialize_payment_ticket(getattr(order, "payment_ticket", None)),
    }
