import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.start import router as start_router
from app.bot.keyboards.main import is_webapp_url
from app.core.config import get_settings
from app.core.runtime import set_public_webapp_url
from app.services.ngrok import ensure_public_webapp_url

settings = get_settings()
logger = logging.getLogger(__name__)


async def configure_bot(bot: Bot, webapp_url: str) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Открыть чайную лавку"),
            BotCommand(command="admin", description="Админ-команды магазина"),
            BotCommand(command="admin_products", description="Товары"),
            BotCommand(command="admin_promotions", description="Акции"),
            BotCommand(command="admin_promo_codes", description="Промокоды"),
        ]
    )
    if is_webapp_url(webapp_url):
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Магазин",
                web_app=WebAppInfo(url=webapp_url),
            )
        )


async def main() -> None:
    if not settings.bot_token or settings.bot_token == "CHANGE_ME":
        logger.warning("BOT_TOKEN is not configured. Bot polling is disabled.")
        await asyncio.Event().wait()
        return

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(start_router)

    webapp_url = await ensure_public_webapp_url(settings)
    set_public_webapp_url(webapp_url)

    await configure_bot(bot, webapp_url)
    logger.info("Bot polling started. WebApp URL: %s", webapp_url)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
