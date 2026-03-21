from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_settings_dep
from app.core.config import Settings
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.order import OrderCreateIn, OrderOut
from app.services.orders import create_order_from_cart, get_order_by_id, serialize_order

router = APIRouter()


@router.post("/create", response_model=OrderOut)
async def create_order(
    payload: OrderCreateIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
):
    order = await create_order_from_cart(session, current_user, payload, settings)
    return serialize_order(order)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    order = await get_order_by_id(session, order_id, current_user.id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден.")
    return serialize_order(order)
