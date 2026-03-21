import logging
from decimal import Decimal
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile

from app.core.config import Settings
from app.models.order import Order

logger = logging.getLogger(__name__)


def format_money(amount: Decimal) -> str:
    value = f"{amount:.0f}" if amount == amount.quantize(Decimal("1")) else f"{amount:.2f}"
    integer, _, fraction = value.partition(".")
    grouped = f"{int(integer):,}".replace(",", " ")
    if fraction and fraction != "00":
        return f"{grouped}.{fraction} сум"
    return f"{grouped} сум"


def build_order_notification(order: Order) -> str:
    lines = [
        "Новый заказ в чайной лавке",
        f"Заказ #{order.id}",
        f"Имя: {order.customer_name}",
        f"Телефон: {order.customer_phone}",
        f"Получение: {'Самовывоз' if order.delivery_type == 'pickup' else 'Доставка по городу'}",
        "",
        "Состав:",
    ]
    for item in order.items:
        product_name = item.product.name if item.product else f"Товар #{item.product_id}"
        pack_suffix = f" ({item.pack_label})" if item.pack_label else ""
        lines.append(f"• {product_name}{pack_suffix} x{item.qty} — {format_money(item.price * item.qty)}")

    if order.discount_amount > 0:
        lines.extend(
            [
                "",
                f"Подытог: {format_money(order.subtotal_amount)}",
                f"Скидка: -{format_money(order.discount_amount)}",
            ]
        )

    lines.extend(
        [
            "",
            f"Итого: {format_money(order.total_amount)}",
            f"Промокод: {order.promo_code or 'Без промокода'}",
            f"Комментарий: {order.comment or 'Без комментария'}",
        ]
    )
    return "\n".join(lines)


def build_payment_ticket_notification(order: Order) -> str:
    ticket = order.payment_ticket
    if ticket is None:
        return build_order_notification(order)

    lines = [
        "Новый тикет оплаты",
        f"Тикет #{ticket.id} по заказу #{order.id}",
        f"Сумма: {format_money(ticket.payment_amount)}",
        f"Имя: {order.customer_name}",
        f"Телефон: {order.customer_phone}",
        f"Контакт для связи: {ticket.customer_contact}",
        f"Получение: {'Самовывоз' if order.delivery_type == 'pickup' else 'Доставка по городу'}",
        "",
        "Состав:",
    ]

    for item in order.items:
        product_name = item.product.name if item.product else f"Товар #{item.product_id}"
        pack_suffix = f" ({item.pack_label})" if item.pack_label else ""
        lines.append(f"• {product_name}{pack_suffix} x{item.qty} — {format_money(item.price * item.qty)}")

    lines.extend(
        [
            "",
            f"Промокод: {order.promo_code or 'Без промокода'}",
            f"Комментарий: {order.comment or 'Без комментария'}",
            "",
            f"/admin_ticket_confirm {ticket.id}",
            f"/admin_ticket_reject {ticket.id}",
        ]
    )
    return "\n".join(lines)


def _resolve_screenshot_path(settings: Settings, screenshot_path: str | None) -> Path | None:
    if not screenshot_path:
        return None

    parts = list(Path(screenshot_path.lstrip("/")).parts)
    if not parts:
        return None
    if parts[0] == "media":
        parts = parts[1:]
    if not parts:
        return None

    file_path = Path(settings.media_dir).joinpath(*parts)
    if file_path.exists():
        return file_path
    return None


async def send_order_notification(settings: Settings, order: Order) -> None:
    if not settings.bot_admin_ids or not settings.bot_token or settings.bot_token == "CHANGE_ME":
        logger.warning("Order notification skipped: bot token or admin ids are not configured.")
        return

    text = build_order_notification(order)
    bot = Bot(token=settings.bot_token)
    try:
        for admin_id in settings.bot_admin_ids:
            await bot.send_message(admin_id, text)
    except Exception:
        logger.exception("Failed to send order notification to admins.")
    finally:
        await bot.session.close()


async def send_payment_ticket_notification(settings: Settings, order: Order) -> None:
    if not settings.bot_admin_ids or not settings.bot_token or settings.bot_token == "CHANGE_ME":
        logger.warning("Payment ticket notification skipped: bot token or admin ids are not configured.")
        return

    text = build_payment_ticket_notification(order)
    screenshot_path = _resolve_screenshot_path(settings, getattr(order.payment_ticket, "screenshot_path", None))
    bot = Bot(token=settings.bot_token)
    try:
        for admin_id in settings.bot_admin_ids:
            if screenshot_path is not None:
                await bot.send_photo(
                    admin_id,
                    FSInputFile(screenshot_path),
                    caption=f"Чек оплаты по заказу #{order.id}",
                )
            await bot.send_message(admin_id, text)
    except Exception:
        logger.exception("Failed to send payment ticket notification to admins.")
    finally:
        await bot.session.close()
