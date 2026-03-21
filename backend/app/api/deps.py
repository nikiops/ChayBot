from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.user import User
from app.services.auth import get_or_create_demo_user, get_or_create_user, validate_telegram_init_data

logger = logging.getLogger(__name__)


async def get_settings_dep() -> Settings:
    return get_settings()


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
    x_telegram_init_data: str | None = Header(default=None),
    x_telegram_user_id: int | None = Header(default=None),
    x_demo_user_id: int | None = Header(default=None),
) -> User:
    authorization = request.headers.get("Authorization")
    init_data = x_telegram_init_data

    if not init_data and authorization and authorization.lower().startswith("tma "):
        init_data = authorization[4:]

    if init_data:
        try:
            identity = validate_telegram_init_data(init_data, settings)
            return await get_or_create_user(session, identity)
        except HTTPException:
            if settings.allow_demo_auth and (x_telegram_user_id or x_demo_user_id):
                fallback_id = x_telegram_user_id or x_demo_user_id
                logger.warning("Telegram initData validation failed, using demo fallback for telegram_id=%s", fallback_id)
                return await get_or_create_demo_user(session, int(fallback_id))
            raise

    if settings.allow_demo_auth:
        demo_id = x_telegram_user_id or x_demo_user_id or settings.demo_user_id
        return await get_or_create_demo_user(session, int(demo_id))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Telegram authorization required.",
    )


async def get_current_admin(
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> User:
    if current_user.telegram_id not in settings.bot_admin_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user
