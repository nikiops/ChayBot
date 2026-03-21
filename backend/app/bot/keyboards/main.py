from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def is_webapp_url(url: str) -> bool:
    return url.lower().startswith("https://")


def build_webapp_url(base_url: str, start: str | None = None) -> str:
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if start:
        query["start"] = start
    else:
        query.pop("start", None)

    path = parts.path or "/"
    return urlunsplit((parts.scheme, parts.netloc, path, urlencode(query), "/"))


def main_menu_keyboard(base_url: str) -> ReplyKeyboardMarkup:
    store_button = (
        KeyboardButton(text="Открыть магазин", web_app=WebAppInfo(url=build_webapp_url(base_url)))
        if is_webapp_url(base_url)
        else KeyboardButton(text="Открыть магазин")
    )
    return ReplyKeyboardMarkup(
        keyboard=[
            [store_button],
            [KeyboardButton(text="Категории"), KeyboardButton(text="Корзина")],
            [KeyboardButton(text="О нас"), KeyboardButton(text="Контакты")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел чайной лавки",
    )


def open_store_keyboard(base_url: str, start: str | None = None, cta: str = "Открыть магазин") -> InlineKeyboardMarkup | None:
    if not is_webapp_url(base_url):
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cta, web_app=WebAppInfo(url=build_webapp_url(base_url, start=start)))]
        ]
    )


def categories_keyboard(base_url: str, categories: list[dict]) -> InlineKeyboardMarkup | None:
    if not is_webapp_url(base_url):
        return None
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category["name"],
            web_app=WebAppInfo(url=build_webapp_url(base_url, start=f"category:{category['slug']}")),
        )
    builder.adjust(2)
    return builder.as_markup()
