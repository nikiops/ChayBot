from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.cart import CartMutationIn, CartOut, CartRemoveIn, CartUpdateIn
from app.schemas.common import MessageResponse
from app.services.cart import add_to_cart, list_cart_items, remove_from_cart, update_cart_item
from app.services.catalog import get_product_by_id
from app.services.pricing import build_cart_payload, get_active_sitewide_promotions, get_promo_code_by_code

router = APIRouter()


@router.get("", response_model=CartOut)
async def get_cart(
    promo_code: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    items = await list_cart_items(session, current_user.id)
    sitewide_promotions = await get_active_sitewide_promotions(session)
    promo = await get_promo_code_by_code(session, promo_code) if promo_code else None
    try:
        return build_cart_payload(items, sitewide_promotions=sitewide_promotions, promo_code=promo)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/add", response_model=MessageResponse)
async def add_cart_item(
    payload: CartMutationIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    product = await get_product_by_id(session, payload.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")

    pack_size = None
    if payload.pack_size_id is not None:
        pack_size = next((item for item in product.pack_sizes if item.id == payload.pack_size_id), None)
        if pack_size is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фасовка не найдена.")
    else:
        pack_size = product.default_pack_size

    await add_to_cart(session, current_user.id, product, pack_size, payload.qty)
    label = f" ({pack_size.label})" if pack_size else ""
    return MessageResponse(message=f"Товар добавлен в корзину{label}.")


@router.post("/update", response_model=MessageResponse)
async def update_cart(
    payload: CartUpdateIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await update_cart_item(session, current_user.id, payload.cart_item_id, payload.qty)
    return MessageResponse(message="Корзина обновлена.")


@router.post("/remove", response_model=MessageResponse)
async def remove_cart_item(
    payload: CartRemoveIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await remove_from_cart(session, current_user.id, payload.cart_item_id)
    return MessageResponse(message="Позиция удалена из корзины.")
