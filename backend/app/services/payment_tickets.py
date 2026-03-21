from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.constants import OrderStatus, PaymentTicketStatus
from app.models.order import Order, OrderItem
from app.models.payment_ticket import PaymentTicket
from app.models.product import Product
from app.models.promo_code import PromoCode
from app.models.user import User
from app.schemas.order import OrderCreateIn
from app.schemas.payment_ticket import PaymentTicketCheckoutIn
from app.services.orders import (
    apply_customer_phone,
    attach_order_items,
    clear_cart_items,
    create_order_entity,
    get_order_by_id,
    load_cart_checkout_context,
)
from app.services.shop_settings import get_payment_settings
from app.services.telegram import send_payment_ticket_notification

MAX_SCREENSHOT_SIZE_BYTES = 8 * 1024 * 1024
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _normalize_extension(upload: UploadFile) -> str:
    filename = upload.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return CONTENT_TYPE_EXTENSIONS.get(upload.content_type or "", ".jpg")


async def _store_screenshot(upload: UploadFile, settings: Settings) -> str:
    if not upload.content_type or not upload.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нужен скриншот в формате изображения.")

    payload = await upload.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Скриншот оплаты не загружен.")
    if len(payload) > MAX_SCREENSHOT_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Скриншот слишком большой. Максимум 8 МБ.")

    extension = _normalize_extension(upload)
    file_name = f"{uuid4().hex}{extension}"
    target_dir = Path(settings.media_dir) / "payment_tickets"
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / file_name
    file_path.write_bytes(payload)
    return f"/media/payment_tickets/{file_name}"


async def get_checkout_payment_config(session: AsyncSession) -> dict[str, str]:
    settings_map = await get_payment_settings(session)
    return {
        "card_number": settings_map["payment_card_number"],
        "card_holder": settings_map["payment_card_holder"],
        "instruction": settings_map["payment_instruction"],
        "contact_hint": settings_map["payment_contact_hint"],
    }


async def create_payment_ticket_from_cart(
    session: AsyncSession,
    user: User,
    payload: PaymentTicketCheckoutIn,
    screenshot: UploadFile,
    settings: Settings,
) -> Order:
    cart_items, cart_payload, promo_code = await load_cart_checkout_context(
        session,
        user,
        promo_code_value=payload.promo_code,
    )

    settings_map = await get_payment_settings(session)
    screenshot_path = await _store_screenshot(screenshot, settings)

    order_payload = OrderCreateIn(
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        comment=payload.comment,
        delivery_type=payload.delivery_type,
        promo_code=payload.promo_code,
    )
    order = create_order_entity(user, order_payload, cart_payload, status_value=OrderStatus.NEW.value)
    session.add(order)
    await session.flush()

    await attach_order_items(session, order, cart_items=cart_items, cart_payload=cart_payload)

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
        elif product is not None:
            if product.stock_qty < cart_item.qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Недостаточно товара '{product.name}' в наличии.",
                )
            product.stock_qty -= cart_item.qty

    if promo_code is not None:
        promo_code.times_used += 1

    session.add(
        PaymentTicket(
            order_id=order.id,
            user_id=user.id,
            customer_contact=payload.customer_contact.strip(),
            payment_amount=cart_payload["total"],
            payment_card_number=settings_map["payment_card_number"],
            payment_card_holder=settings_map["payment_card_holder"],
            instructions=settings_map["payment_instruction"],
            screenshot_path=screenshot_path,
            status=PaymentTicketStatus.NEW.value,
        )
    )

    await clear_cart_items(session, cart_items)
    apply_customer_phone(user, payload.customer_phone)
    await session.commit()

    refreshed_order = await get_order_by_id(session, order.id, user.id)
    if refreshed_order is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Заказ не найден.")

    await send_payment_ticket_notification(settings, refreshed_order)
    return refreshed_order


async def get_payment_ticket_by_id(
    session: AsyncSession,
    ticket_id: int,
    *,
    user_id: int | None = None,
) -> PaymentTicket | None:
    stmt = (
        select(PaymentTicket)
        .options(selectinload(PaymentTicket.order))
        .where(PaymentTicket.id == ticket_id)
    )
    if user_id is not None:
        stmt = stmt.where(PaymentTicket.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().unique().one_or_none()


async def list_payment_tickets(session: AsyncSession, *, limit: int = 50) -> list[PaymentTicket]:
    result = await session.execute(
        select(PaymentTicket)
        .options(
            selectinload(PaymentTicket.order)
            .selectinload(Order.items)
            .selectinload(OrderItem.product),
            selectinload(PaymentTicket.order)
            .selectinload(Order.items)
            .selectinload(OrderItem.pack_size),
        )
        .order_by(PaymentTicket.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().unique().all())


def serialize_admin_payment_ticket(ticket: PaymentTicket) -> dict:
    order = ticket.order
    items_summary: list[str] = []
    if order is not None:
        for item in order.items:
            product_name = item.product.name if item.product else f"Товар #{item.product_id}"
            pack_label = f" / {item.pack_label}" if item.pack_label else ""
            items_summary.append(f"{product_name}{pack_label} x{item.qty}")

    return {
        "id": ticket.id,
        "order_id": ticket.order_id,
        "order_status": order.status if order else OrderStatus.NEW.value,
        "customer_name": order.customer_name if order else "Без имени",
        "customer_phone": order.customer_phone if order else "—",
        "customer_contact": ticket.customer_contact,
        "delivery_type": order.delivery_type if order else "pickup",
        "payment_amount": ticket.payment_amount,
        "promo_code": order.promo_code if order else None,
        "screenshot_path": ticket.screenshot_path,
        "status": ticket.status,
        "admin_comment": ticket.admin_comment,
        "created_at": ticket.created_at,
        "reviewed_at": ticket.reviewed_at,
        "items_summary": items_summary,
    }


async def _get_ticket_for_review(session: AsyncSession, ticket_id: int) -> PaymentTicket | None:
    result = await session.execute(
        select(PaymentTicket)
        .options(
            selectinload(PaymentTicket.order)
            .selectinload(Order.items)
            .selectinload(OrderItem.product),
            selectinload(PaymentTicket.order)
            .selectinload(Order.items)
            .selectinload(OrderItem.pack_size),
        )
        .where(PaymentTicket.id == ticket_id)
    )
    return result.scalars().unique().one_or_none()


async def confirm_payment_ticket(
    session: AsyncSession,
    ticket_id: int,
    *,
    admin_comment: str | None = None,
) -> PaymentTicket | None:
    ticket = await _get_ticket_for_review(session, ticket_id)
    if ticket is None:
        return None
    if ticket.status != PaymentTicketStatus.NEW.value or ticket.order.status != OrderStatus.NEW.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Тикет уже обработан.")

    ticket.status = PaymentTicketStatus.CONFIRMED.value
    ticket.admin_comment = admin_comment
    ticket.reviewed_at = datetime.now(timezone.utc)
    ticket.order.status = OrderStatus.CONFIRMED.value
    await session.commit()
    return await _get_ticket_for_review(session, ticket_id)


async def reject_payment_ticket(
    session: AsyncSession,
    ticket_id: int,
    *,
    admin_comment: str | None = None,
) -> PaymentTicket | None:
    ticket = await _get_ticket_for_review(session, ticket_id)
    if ticket is None:
        return None
    if ticket.status != PaymentTicketStatus.NEW.value or ticket.order.status != OrderStatus.NEW.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Тикет уже обработан.")

    for item in ticket.order.items:
        if item.pack_size is not None:
            item.pack_size.stock_qty += item.qty
        elif item.product is not None:
            item.product.stock_qty += item.qty

    if ticket.order.promo_code:
        promo_result = await session.execute(select(PromoCode).where(PromoCode.code == ticket.order.promo_code))
        promo_code = promo_result.scalar_one_or_none()
        if promo_code is not None and promo_code.times_used > 0:
            promo_code.times_used -= 1

    ticket.status = PaymentTicketStatus.REJECTED.value
    ticket.admin_comment = admin_comment
    ticket.reviewed_at = datetime.now(timezone.utc)
    ticket.order.status = OrderStatus.CANCELLED.value
    await session.commit()
    return await _get_ticket_for_review(session, ticket_id)
