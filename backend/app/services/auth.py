import hashlib
import hmac
import json
import time
from dataclasses import dataclass
import logging
from urllib.parse import parse_qsl

from fastapi import HTTPException, status
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User

logger = logging.getLogger(__name__)

TELEGRAM_WEBAPP_PUBLIC_KEY_PRODUCTION = bytes.fromhex(
    "e7bf03a2fa4602af4580703d88dda5bb59f32ed8b02a56c187fe7d34caed242d"
)


@dataclass(slots=True)
class TelegramIdentity:
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None


def _parse_init_data(init_data: str) -> dict[str, str]:
    return dict(parse_qsl(init_data, keep_blank_values=True))


def _build_data_check_string(payload: dict[str, str], *, exclude_signature: bool) -> str:
    excluded = {"hash"}
    if exclude_signature:
        excluded.add("signature")
    return "\n".join(
        f"{key}={value}"
        for key, value in sorted(payload.items())
        if key not in excluded
    )


def _base64url_decode(value: str) -> bytes:
    import base64

    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _validate_via_hash(payload: dict[str, str], bot_token: str) -> bool:
    received_hash = payload.get("hash")
    if not received_hash:
        return False

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    # Telegram clients may include "signature" in initData.
    # Try both variants to stay compatible with clients that do or don't
    # account for it when constructing the hash payload.
    for exclude_signature in (True, False):
        data_check_string = _build_data_check_string(payload, exclude_signature=exclude_signature)
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(calculated_hash, received_hash):
            return True

    return False


def _validate_via_public_signature(payload: dict[str, str], bot_token: str) -> bool:
    signature = payload.get("signature")
    if not signature:
        return False

    bot_id = bot_token.split(":", 1)[0].strip()
    if not bot_id:
        return False

    data_check_string = (
        f"{bot_id}:WebAppData\n"
        f"{_build_data_check_string(payload, exclude_signature=True)}"
    )

    try:
        signature_bytes = _base64url_decode(signature)
        Ed25519PublicKey.from_public_bytes(TELEGRAM_WEBAPP_PUBLIC_KEY_PRODUCTION).verify(
            signature_bytes,
            data_check_string.encode(),
        )
        return True
    except Exception:
        return False


def validate_telegram_init_data(init_data: str, settings: Settings) -> TelegramIdentity:
    if not settings.bot_token or settings.bot_token == "CHANGE_ME":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="BOT_TOKEN is not configured.",
        )

    payload = _parse_init_data(init_data)
    if "hash" not in payload and "signature" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Telegram hash.")

    is_valid = _validate_via_hash(payload, settings.bot_token) or _validate_via_public_signature(
        payload,
        settings.bot_token,
    )
    if not is_valid:
        logger.warning(
            "Telegram initData validation failed; keys=%s has_hash=%s has_signature=%s auth_date=%s",
            ",".join(sorted(payload.keys())),
            "hash" in payload,
            "signature" in payload,
            payload.get("auth_date"),
        )
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
