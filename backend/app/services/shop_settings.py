from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_setting import AdminSetting

PAYMENT_SETTING_DEFAULTS = {
    "payment_card_number": "8600 1234 5678 9012",
    "payment_card_holder": "Golden Tea",
    "payment_instruction": (
        "Переведите точную сумму заказа на карту, затем прикрепите скриншот чека. "
        "Администратор проверит оплату и подтвердит заказ в Telegram."
    ),
    "payment_contact_hint": "Укажите номер телефона или @telegram, по которому с вами удобно связаться.",
}

PAYMENT_SETTING_KEYS = tuple(PAYMENT_SETTING_DEFAULTS.keys())


async def get_payment_settings(session: AsyncSession) -> dict[str, str]:
    result = await session.execute(
        select(AdminSetting).where(AdminSetting.key.in_(PAYMENT_SETTING_KEYS))
    )
    payload = dict(PAYMENT_SETTING_DEFAULTS)
    for item in result.scalars().all():
        payload[item.key] = item.value
    return payload


async def update_payment_settings(
    session: AsyncSession,
    *,
    card_number: str,
    card_holder: str | None,
    instruction: str,
    contact_hint: str,
) -> dict[str, str]:
    values = {
        "payment_card_number": card_number.strip(),
        "payment_card_holder": (card_holder or "").strip() or PAYMENT_SETTING_DEFAULTS["payment_card_holder"],
        "payment_instruction": instruction.strip(),
        "payment_contact_hint": contact_hint.strip(),
    }

    result = await session.execute(
        select(AdminSetting).where(AdminSetting.key.in_(PAYMENT_SETTING_KEYS))
    )
    existing = {item.key: item for item in result.scalars().all()}

    for key, value in values.items():
        setting = existing.get(key)
        if setting is None:
            session.add(AdminSetting(key=key, value=value))
        else:
            setting.value = value

    await session.commit()
    return await get_payment_settings(session)
