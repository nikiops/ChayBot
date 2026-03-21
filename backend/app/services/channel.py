from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.constants import ChannelSourceType
from app.models.channel_post import ChannelPost
from app.models.product import Product
from app.models.promotion import Promotion
from app.services.pricing import get_active_sitewide_promotions, serialize_product
from app.services.media import resolve_media_path
from app.services.telegram import format_money
from app.utils.deeplinks import build_start_link


def _channel_button(url: str, text: str = "Открыть магазин") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, url=url)]]
    )


def _cap_caption(text: str) -> str:
    return text[:1020] + "..." if len(text) > 1023 else text


def _discount_label(discount_type: str, discount_value: Decimal) -> str:
    if discount_type == "percent":
        return f"-{discount_value:.0f}%"
    return f"-{format_money(discount_value)}"


def _resolve_photo_source(settings: Settings, image_url: str | None) -> str | FSInputFile | None:
    if not image_url:
        return None

    media_path = resolve_media_path(settings, image_url)
    if media_path is not None:
        return FSInputFile(Path(media_path))
    return image_url


def build_product_post(product_payload: dict, settings: Settings) -> tuple[str, str, str]:
    pack_label = product_payload["default_pack_size"]["label"]
    old_price = product_payload["old_price"]
    deeplink = build_start_link(settings.bot_username, f"product:{product_payload['slug']}")

    lines = [
        product_payload["name"],
        product_payload["short_description"],
        "",
        f"Фасовка: {pack_label}",
        f"Цена: {format_money(product_payload['price'])}",
    ]
    if old_price:
        lines.append(f"Вместо: {format_money(old_price)}")
    if product_payload["default_pack_size"].get("promotion_title"):
        lines.append(f"Акция: {product_payload['default_pack_size']['promotion_title']}")
    lines.extend(
        [
            "",
            "Нажмите кнопку ниже: бот откроет витрину и переведет в карточку товара.",
        ]
    )

    return (
        product_payload["name"],
        _cap_caption("\n".join(lines)),
        deeplink,
    )


def build_promotion_post(promotion: Promotion, settings: Settings) -> tuple[str, str, str]:
    deeplink = build_start_link(settings.bot_username, f"promo:{promotion.slug}")
    scope = "на весь каталог" if promotion.is_sitewide else "на выбранные товары"
    lines = [
        promotion.title,
        promotion.description,
        "",
        f"Формат: {scope}",
        f"Скидка: {_discount_label(promotion.discount_type, promotion.discount_value)}",
        "",
        "Нажмите кнопку ниже: бот откроет витрину с товарами, участвующими в акции.",
    ]
    return promotion.title, _cap_caption("\n".join(lines)), deeplink


async def _publish_message(
    settings: Settings,
    *,
    title: str,
    caption: str,
    image_url: str | None,
    deep_link: str,
    existing_post: ChannelPost | None,
) -> int:
    bot = Bot(token=settings.bot_token)
    markup = _channel_button(deep_link)
    try:
        if existing_post and existing_post.message_id:
            if image_url:
                await bot.edit_message_caption(
                    chat_id=settings.channel_chat_id,
                    message_id=existing_post.message_id,
                    caption=caption,
                    reply_markup=markup,
                )
            else:
                await bot.edit_message_text(
                    text=caption,
                    chat_id=settings.channel_chat_id,
                    message_id=existing_post.message_id,
                    reply_markup=markup,
                )
            return existing_post.message_id

        if image_url:
            photo_source = _resolve_photo_source(settings, image_url)
            message = await bot.send_photo(
                chat_id=settings.channel_chat_id,
                photo=photo_source,
                caption=caption,
                reply_markup=markup,
            )
        else:
            message = await bot.send_message(
                chat_id=settings.channel_chat_id,
                text=caption,
                reply_markup=markup,
            )
        return message.message_id
    finally:
        await bot.session.close()


async def _get_last_channel_post(
    session: AsyncSession,
    *,
    source_type: str,
    source_id: int,
    channel_chat_id: str,
) -> ChannelPost | None:
    result = await session.execute(
        select(ChannelPost)
        .where(
            ChannelPost.source_type == source_type,
            ChannelPost.source_id == source_id,
            ChannelPost.channel_chat_id == channel_chat_id,
        )
        .order_by(desc(ChannelPost.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def publish_product_to_channel(
    session: AsyncSession,
    settings: Settings,
    *,
    product: Product,
) -> ChannelPost:
    sitewide_promotions = await get_active_sitewide_promotions(session)
    product_payload = serialize_product(product, sitewide_promotions=sitewide_promotions)
    title, caption, deep_link = build_product_post(product_payload, settings)
    existing_post = await _get_last_channel_post(
        session,
        source_type=ChannelSourceType.PRODUCT.value,
        source_id=product.id,
        channel_chat_id=settings.channel_chat_id,
    )

    message_id = await _publish_message(
        settings,
        title=title,
        caption=caption,
        image_url=product.image_url,
        deep_link=deep_link,
        existing_post=existing_post,
    )

    if existing_post is None:
        existing_post = ChannelPost(
            source_type=ChannelSourceType.PRODUCT.value,
            source_id=product.id,
            channel_chat_id=settings.channel_chat_id,
            title=title,
            image_url=product.image_url,
            caption=caption,
            deep_link=deep_link,
            message_id=message_id,
            is_active=True,
        )
        session.add(existing_post)
    else:
        existing_post.title = title
        existing_post.image_url = product.image_url
        existing_post.caption = caption
        existing_post.deep_link = deep_link
        existing_post.message_id = message_id
        existing_post.is_active = True

    await session.commit()
    await session.refresh(existing_post)
    return existing_post


async def publish_promotion_to_channel(
    session: AsyncSession,
    settings: Settings,
    *,
    promotion: Promotion,
) -> ChannelPost:
    title, caption, deep_link = build_promotion_post(promotion, settings)
    existing_post = await _get_last_channel_post(
        session,
        source_type=ChannelSourceType.PROMOTION.value,
        source_id=promotion.id,
        channel_chat_id=settings.channel_chat_id,
    )

    message_id = await _publish_message(
        settings,
        title=title,
        caption=caption,
        image_url=promotion.image_url,
        deep_link=deep_link,
        existing_post=existing_post,
    )

    if existing_post is None:
        existing_post = ChannelPost(
            source_type=ChannelSourceType.PROMOTION.value,
            source_id=promotion.id,
            channel_chat_id=settings.channel_chat_id,
            title=title,
            image_url=promotion.image_url,
            caption=caption,
            deep_link=deep_link,
            message_id=message_id,
            is_active=True,
        )
        session.add(existing_post)
    else:
        existing_post.title = title
        existing_post.image_url = promotion.image_url
        existing_post.caption = caption
        existing_post.deep_link = deep_link
        existing_post.message_id = message_id
        existing_post.is_active = True

    await session.commit()
    await session.refresh(existing_post)
    return existing_post


async def list_channel_posts(session: AsyncSession, limit: int = 50) -> list[ChannelPost]:
    result = await session.execute(
        select(ChannelPost).order_by(desc(ChannelPost.created_at)).limit(limit)
    )
    return list(result.scalars().all())


async def get_product_for_channel(session: AsyncSession, product_id: int) -> Product | None:
    result = await session.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.pack_sizes),
            selectinload(Product.promotions),
        )
        .where(Product.id == product_id)
    )
    return result.scalar_one_or_none()


async def get_promotion_for_channel(session: AsyncSession, promotion_id: int) -> Promotion | None:
    result = await session.execute(
        select(Promotion)
        .options(selectinload(Promotion.products))
        .where(Promotion.id == promotion_id)
    )
    return result.scalar_one_or_none()
