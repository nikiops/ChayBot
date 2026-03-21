from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main import categories_keyboard, is_webapp_url, main_menu_keyboard, open_store_keyboard
from app.core.config import get_settings
from app.core.runtime import get_public_webapp_url
from app.db.session import AsyncSessionLocal
from app.services.catalog import list_categories

router = Router()
settings = get_settings()


WELCOME_TEXT = (
    "Чайная лавка внутри Telegram\n\n"
    "Подберем китайский чай по вкусу: от глубокого пуэра до воздушного белого чая, "
    "добавим подарочные наборы и красивую посуду для домашней церемонии."
)

ABOUT_TEXT = (
    "Мы собираем спокойную и современную чайную витрину:\n"
    "• китайский чай с красивым вкусом и понятным описанием\n"
    "• подбор по настроению и вкусовому профилю\n"
    "• подарочные наборы\n"
    "• аксессуары и чайная посуда\n"
    "• оформление заказа прямо внутри Telegram"
)


def _resolve_start_payload(payload: str | None) -> tuple[str, str]:
    if not payload:
        return "store", "Открыть магазин"
    if payload.startswith("category_"):
        slug = payload.replace("category_", "", 1)
        return f"category:{slug}", "Открыть раздел"
    if payload.startswith("category:"):
        return payload, "Открыть раздел"
    if payload == "cart":
        return "cart", "Перейти в корзину"
    if payload.startswith("product:"):
        return payload, "Открыть товар"
    if payload.startswith("promo_"):
        return f"promo:{payload.replace('promo_', '', 1)}", "Посмотреть акцию"
    if payload.startswith("promo:"):
        return payload, "Посмотреть акцию"
    return payload, "Открыть магазин"


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    payload = None
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) > 1:
        payload = parts[1].strip()

    webapp_url = get_public_webapp_url()
    start_target, cta = _resolve_start_payload(payload)
    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(webapp_url),
    )
    if is_webapp_url(webapp_url):
        await message.answer(
            "Откройте витрину, чтобы посмотреть подборки, каталог и оформить заказ.",
            reply_markup=open_store_keyboard(webapp_url, start_target, cta),
        )
    else:
        await message.answer(
            "Витрина еще не получила публичный HTTPS-адрес. Я автоматически подключу кнопку магазина сразу после старта туннеля."
        )


@router.message(F.text == "Открыть магазин")
async def open_store_handler(message: Message) -> None:
    webapp_url = get_public_webapp_url()
    if is_webapp_url(webapp_url):
        await message.answer(
            "Мини-приложение откроет каталог, подборки и ваши текущие позиции в корзине.",
            reply_markup=open_store_keyboard(webapp_url),
        )
    else:
        await message.answer(
            "Туннель витрины еще запускается. Попробуйте еще раз через несколько секунд."
        )


@router.message(F.text == "Категории")
async def categories_handler(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        categories = await list_categories(session)

    webapp_url = get_public_webapp_url()
    if is_webapp_url(webapp_url):
        await message.answer(
            "Выберите категорию и откройте нужный раздел витрины.",
            reply_markup=categories_keyboard(webapp_url, categories),
        )
    else:
        categories_text = "\n".join(f"• {category['name']}" for category in categories)
        await message.answer(
            "Категории магазина:\n"
            f"{categories_text}\n\n"
            "HTTPS-ссылка витрины еще готовится, поэтому пока отправляю список текстом."
        )


@router.message(F.text == "Корзина")
async def cart_handler(message: Message) -> None:
    webapp_url = get_public_webapp_url()
    if is_webapp_url(webapp_url):
        await message.answer(
            "В корзине будут сохранены выбранные позиции, количество и итоговая сумма.",
            reply_markup=open_store_keyboard(webapp_url, "cart", "Открыть корзину"),
        )
    else:
        await message.answer(
            "Туннель витрины еще запускается. Как только HTTPS-ссылка поднимется, корзина откроется в Mini App."
        )


@router.message(F.text == "О нас")
async def about_handler(message: Message) -> None:
    await message.answer(ABOUT_TEXT)


@router.message(F.text == "Контакты")
async def contacts_handler(message: Message) -> None:
    await message.answer(
        "Контакты чайной лавки\n\n"
        f"Telegram: {settings.contact_telegram}\n"
        f"Телефон: {settings.contact_phone}\n"
        f"Город: {settings.contact_city}\n"
        f"Часы работы: {settings.contact_hours}"
    )
