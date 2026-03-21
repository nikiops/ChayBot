import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User


@dataclass(slots=True)
class TelegramIdentity:
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None


def _parse_init_data(init_data: str) -> dict[str, str]:
    return dict(parse_qsl(init_data, keep_blank_values=True))


def validate_telegram_init_data(init_data: str, settings: Settings) -> TelegramIdentity:
    if not settings.bot_token or settings.bot_token == "CHANGE_ME":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="BOT_TOKEN is not configured.",
        )

    payload = _parse_init_data(init_data)
    received_hash = payload.get("hash")
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telegram hash.")

    data_check_items = [
        f"{key}={value}"
        for key, value in sorted(payload.items())
        if key not in {"hash", "signature"}
    ]
    data_check_string = "\n".join(data_check_items)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=settings.bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram signature.")

    auth_date = int(payload.get("auth_date", "0"))
    if settings.telegram_init_data_lifetime and (time.time() - auth_date) > settings.telegram_init_data_lifetime:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram auth data expired.")

    raw_user = payload.get("user")
    if not raw_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram user payload missing.")

    user_payload = json.loads(raw_user)
    return TelegramIdentity(
        telegram_id=int(user_payload["id"]),
        username=user_payload.get("username"),
        first_name=user_payload.get("first_name", "Гость"),
        last_name=user_payload.get("last_name"),
    )


async def get_or_create_user(session: AsyncSession, identity: TelegramIdentity) -> User:
    result = await session.execute(select(User).where(User.telegram_id == identity.telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=identity.telegram_id,
            username=identity.username,
            first_name=identity.first_name,
            last_name=identity.last_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    user.username = identity.username
    user.first_name = identity.first_name
    user.last_name = identity.last_name
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_demo_user(session: AsyncSession, telegram_id: int) -> User:
    identity = TelegramIdentity(
        telegram_id=telegram_id,
        username="demo_user",
        first_name="Демо",
        last_name="Покупатель",
    )
    return await get_or_create_user(session, identity)

