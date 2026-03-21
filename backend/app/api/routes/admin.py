from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_settings_dep
from app.core.config import Settings
from app.db.session import get_db_session
from app.schemas.admin import (
    AdminChannelPostOut,
    AdminOrderOut,
    AdminPaymentSettingsIn,
    AdminPaymentSettingsOut,
    AdminPaymentTicketOut,
    AdminProductCreateIn,
    AdminProductOut,
    AdminProductUpdateIn,
    AdminUploadedImageOut,
    AdminPromoCodeCreateIn,
    AdminPromoCodeOut,
    AdminPromoCodeUpdateIn,
    AdminPromotionCreateIn,
    AdminPromotionOut,
    AdminStatsOut,
)
from app.schemas.common import MessageResponse
from app.services.admin import (
    create_admin_product,
    create_promo_code,
    create_promotion,
    delete_admin_product,
    get_admin_stats,
    list_admin_channel_posts,
    list_admin_orders,
    list_admin_products,
    list_promo_codes,
    list_promotions,
    publish_product_post,
    publish_promotion_post,
    toggle_product_active,
    toggle_promo_code_active,
    toggle_promotion_active,
    update_admin_product,
    update_promo_code,
)
from app.services.payment_tickets import (
    confirm_payment_ticket,
    list_payment_tickets,
    reject_payment_ticket,
    serialize_admin_payment_ticket,
)
from app.services.media import store_product_image
from app.services.shop_settings import get_payment_settings, update_payment_settings

router = APIRouter()


def _promotion_out(promotion) -> dict:
    return {
        "id": promotion.id,
        "title": promotion.title,
        "slug": promotion.slug,
        "description": promotion.description,
        "image_url": promotion.image_url,
        "badge_text": promotion.badge_text,
        "discount_type": promotion.discount_type,
        "discount_value": promotion.discount_value,
        "is_sitewide": promotion.is_sitewide,
        "is_active": promotion.is_active,
        "starts_at": promotion.starts_at,
        "ends_at": promotion.ends_at,
        "created_at": promotion.created_at,
        "product_ids": [product.id for product in promotion.products],
    }


def _promo_code_out(promo_code) -> dict:
    return {
        "id": promo_code.id,
        "code": promo_code.code,
        "title": promo_code.title,
        "description": promo_code.description,
        "discount_type": promo_code.discount_type,
        "discount_value": promo_code.discount_value,
        "is_sitewide": promo_code.is_sitewide,
        "minimum_order_amount": promo_code.minimum_order_amount,
        "max_uses": promo_code.max_uses,
        "is_active": promo_code.is_active,
        "starts_at": promo_code.starts_at,
        "ends_at": promo_code.ends_at,
        "times_used": promo_code.times_used,
        "created_at": promo_code.created_at,
        "product_ids": [product.id for product in promo_code.products],
    }


def _payment_settings_out(settings_map: dict[str, str]) -> dict:
    return {
        "card_number": settings_map["payment_card_number"],
        "card_holder": settings_map["payment_card_holder"],
        "instruction": settings_map["payment_instruction"],
        "contact_hint": settings_map["payment_contact_hint"],
    }


@router.get("/stats", response_model=AdminStatsOut)
async def admin_stats(
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    return await get_admin_stats(session)


@router.get("/orders", response_model=list[AdminOrderOut])
async def admin_orders(
    limit: int = Query(default=10, ge=1, le=100),
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_admin_orders(session, limit=limit)


@router.get("/products", response_model=list[AdminProductOut])
async def admin_products(
    limit: int = Query(default=100, ge=1, le=200),
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_admin_products(session, limit=limit)


@router.post("/products", response_model=AdminProductOut, status_code=status.HTTP_201_CREATED)
async def admin_create_product(
    payload: AdminProductCreateIn,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    return await create_admin_product(session, payload)


@router.post("/products/image-upload", response_model=AdminUploadedImageOut, status_code=status.HTTP_201_CREATED)
async def admin_upload_product_image(
    image: UploadFile = File(...),
    _: object = Depends(get_current_admin),
    settings: Settings = Depends(get_settings_dep),
):
    return await store_product_image(image, settings)


@router.put("/products/{product_id}", response_model=AdminProductOut)
async def admin_update_product(
    product_id: int,
    payload: AdminProductUpdateIn,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    product = await update_admin_product(session, product_id, payload)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    return product


@router.post("/products/{product_id}/toggle", response_model=MessageResponse)
async def admin_toggle_product(
    product_id: int,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    product = await toggle_product_active(session, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    action = "включен" if product.is_active else "отключен"
    return MessageResponse(message=f"Товар '{product.name}' {action}.")


@router.delete("/products/{product_id}", response_model=MessageResponse)
async def admin_delete_product(
    product_id: int,
    _: object = Depends(get_current_admin),
    settings: Settings = Depends(get_settings_dep),
    session: AsyncSession = Depends(get_db_session),
):
    product_name = await delete_admin_product(session, settings, product_id)
    if product_name is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="РўРѕРІР°СЂ РЅРµ РЅР°Р№РґРµРЅ.")
    return MessageResponse(message=f"Товар '{product_name}' удален.")


@router.get("/promotions", response_model=list[AdminPromotionOut])
async def admin_promotions(
    limit: int = Query(default=100, ge=1, le=200),
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    promotions = await list_promotions(session, limit=limit)
    return [_promotion_out(promotion) for promotion in promotions]


@router.post("/promotions", response_model=AdminPromotionOut)
async def admin_create_promotion(
    payload: AdminPromotionCreateIn,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    promotion = await create_promotion(session, payload)
    return _promotion_out(promotion)


@router.post("/promotions/{promotion_id}/toggle", response_model=MessageResponse)
async def admin_toggle_promotion(
    promotion_id: int,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    promotion = await toggle_promotion_active(session, promotion_id)
    if promotion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Акция не найдена.")
    action = "включена" if promotion.is_active else "отключена"
    return MessageResponse(message=f"Акция '{promotion.title}' {action}.")


@router.get("/promo-codes", response_model=list[AdminPromoCodeOut])
async def admin_promo_codes(
    limit: int = Query(default=100, ge=1, le=200),
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    promo_codes = await list_promo_codes(session, limit=limit)
    return [_promo_code_out(promo_code) for promo_code in promo_codes]


@router.post("/promo-codes", response_model=AdminPromoCodeOut, status_code=status.HTTP_201_CREATED)
async def admin_create_promo_code(
    payload: AdminPromoCodeCreateIn,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    promo_code = await create_promo_code(session, payload)
    return _promo_code_out(promo_code)


@router.put("/promo-codes/{promo_code_id}", response_model=AdminPromoCodeOut)
async def admin_update_promo_code(
    promo_code_id: int,
    payload: AdminPromoCodeUpdateIn,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    promo_code = await update_promo_code(session, promo_code_id, payload)
    if promo_code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Промокод не найден.")
    return _promo_code_out(promo_code)


@router.post("/promo-codes/{promo_code_id}/toggle", response_model=MessageResponse)
async def admin_toggle_promo_code(
    promo_code_id: int,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    promo_code = await toggle_promo_code_active(session, promo_code_id)
    if promo_code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Промокод не найден.")
    action = "включен" if promo_code.is_active else "отключен"
    return MessageResponse(message=f"Промокод '{promo_code.code}' {action}.")


@router.get("/channel/posts", response_model=list[AdminChannelPostOut])
async def admin_channel_posts(
    limit: int = Query(default=50, ge=1, le=200),
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_admin_channel_posts(session, limit=limit)


@router.get("/payment-tickets", response_model=list[AdminPaymentTicketOut])
async def admin_payment_tickets(
    limit: int = Query(default=50, ge=1, le=200),
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    tickets = await list_payment_tickets(session, limit=limit)
    return [serialize_admin_payment_ticket(ticket) for ticket in tickets]


@router.post("/payment-tickets/{ticket_id}/confirm", response_model=AdminPaymentTicketOut)
async def admin_confirm_payment_ticket(
    ticket_id: int,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    ticket = await confirm_payment_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тикет не найден.")
    return serialize_admin_payment_ticket(ticket)


@router.post("/payment-tickets/{ticket_id}/reject", response_model=AdminPaymentTicketOut)
async def admin_reject_payment_ticket(
    ticket_id: int,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    ticket = await reject_payment_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тикет не найден.")
    return serialize_admin_payment_ticket(ticket)


@router.get("/settings/payment", response_model=AdminPaymentSettingsOut)
async def admin_payment_settings(
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    return _payment_settings_out(await get_payment_settings(session))


@router.put("/settings/payment", response_model=AdminPaymentSettingsOut)
async def admin_update_payment_settings(
    payload: AdminPaymentSettingsIn,
    _: object = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
):
    settings_map = await update_payment_settings(
        session,
        card_number=payload.card_number,
        card_holder=payload.card_holder,
        instruction=payload.instruction,
        contact_hint=payload.contact_hint,
    )
    return _payment_settings_out(settings_map)


@router.post("/channel/products/{product_id}/publish", response_model=AdminChannelPostOut)
async def admin_publish_product(
    product_id: int,
    _: object = Depends(get_current_admin),
    settings: Settings = Depends(get_settings_dep),
    session: AsyncSession = Depends(get_db_session),
):
    post = await publish_product_post(session, settings, product_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    return post


@router.post("/channel/promotions/{promotion_id}/publish", response_model=AdminChannelPostOut)
async def admin_publish_promotion(
    promotion_id: int,
    _: object = Depends(get_current_admin),
    settings: Settings = Depends(get_settings_dep),
    session: AsyncSession = Depends(get_db_session),
):
    post = await publish_promotion_post(session, settings, promotion_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Акция не найдена.")
    return post
