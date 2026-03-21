from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_settings_dep
from app.core.config import Settings
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.order import OrderOut
from app.schemas.payment_ticket import CheckoutPaymentConfigOut, PaymentTicketCheckoutIn, PaymentTicketOut
from app.services.orders import serialize_order, serialize_payment_ticket
from app.services.payment_tickets import (
    create_payment_ticket_from_cart,
    get_checkout_payment_config,
    get_payment_ticket_by_id,
)

router = APIRouter()


@router.get("/checkout-config", response_model=CheckoutPaymentConfigOut)
async def checkout_config(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    del current_user
    return await get_checkout_payment_config(session)


@router.post("/create", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_payment_ticket(
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    customer_contact: str = Form(...),
    comment: str | None = Form(default=None),
    delivery_type: str = Form(...),
    promo_code: str | None = Form(default=None),
    payment_screenshot: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
):
    try:
        payload = PaymentTicketCheckoutIn(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_contact=customer_contact,
            comment=comment,
            delivery_type=delivery_type,
            promo_code=promo_code,
        )
    except ValidationError as exc:
        first_error = exc.errors()[0]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=first_error.get("msg", "Проверьте данные для оплаты."),
        ) from exc
    order = await create_payment_ticket_from_cart(session, current_user, payload, payment_screenshot, settings)
    return serialize_order(order)


@router.get("/{ticket_id}", response_model=PaymentTicketOut)
async def get_payment_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    ticket = await get_payment_ticket_by_id(session, ticket_id, user_id=current_user.id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тикет не найден.")
    return serialize_payment_ticket(ticket)
