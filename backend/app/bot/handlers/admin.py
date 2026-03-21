from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.admin import (
    get_admin_stats,
    list_admin_orders,
    list_admin_products,
    list_promo_codes,
    list_promotions,
    publish_product_post,
    publish_promotion_post,
    toggle_product_active,
)
from app.services.payment_tickets import (
    confirm_payment_ticket,
    list_payment_tickets,
    reject_payment_ticket,
    serialize_admin_payment_ticket,
)
from app.services.telegram import format_money

router = Router()
settings = get_settings()


async def _plain_answer(message: Message, text: str) -> None:
    await message.answer(text, parse_mode=None)


def _is_admin(message: Message) -> bool:
    user = message.from_user
    return bool(user and user.id in settings.bot_admin_ids)


async def _reject_non_admin(message: Message) -> bool:
    if _is_admin(message):
        return False
    await _plain_answer(message, "Эта команда доступна только администраторам магазина.")
    return True


@router.message(Command("admin"))
async def admin_help_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    await _plain_answer(
        message,
        "Админ-команды магазина:\n"
        "/admin_stats — статистика\n"
        "/admin_orders — последние заказы\n"
        "/admin_products — список товаров\n"
        "/admin_promotions — акции\n"
        "/admin_promo_codes — промокоды\n"
        "/admin_tickets — тикеты оплаты\n"
        "/admin_toggle (id) — включить или отключить товар\n"
        "/admin_publish_product (id) — отправить товар в канал\n"
        "/admin_publish_promotion (id) — отправить акцию в канал\n"
        "/admin_ticket_confirm (id) — подтвердить оплату\n"
        "/admin_ticket_reject (id) — отклонить оплату"
    )


@router.message(Command("admin_stats"))
async def admin_stats_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    async with AsyncSessionLocal() as session:
        stats = await get_admin_stats(session)
    await _plain_answer(
        message,
        "Статистика магазина\n\n"
        f"Пользователи: {stats['users_count']}\n"
        f"Заказы: {stats['orders_count']}\n"
        f"Товары: {stats['products_count']}\n"
        f"Активные товары: {stats['active_products_count']}\n"
        f"Акции: {stats['promotions_count']}\n"
        f"Промокоды: {stats['promo_codes_count']}\n"
        f"Посты канала: {stats['channel_posts_count']}\n"
        f"Тикеты оплаты: {stats['payment_tickets_count']}\n"
        f"На проверке: {stats['pending_payment_tickets_count']}"
    )


@router.message(Command("admin_orders"))
async def admin_orders_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    async with AsyncSessionLocal() as session:
        orders = await list_admin_orders(session, limit=10)
    if not orders:
        await _plain_answer(message, "Заказов пока нет.")
        return
    lines = ["Последние заказы:"]
    for order in orders:
        promo = f" • промокод {order.promo_code}" if order.promo_code else ""
        lines.append(f"#{order.id} • {order.customer_name} • {format_money(order.total_amount)} • {order.status}{promo}")
    await _plain_answer(message, "\n".join(lines))


@router.message(Command("admin_products"))
async def admin_products_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    async with AsyncSessionLocal() as session:
        products = await list_admin_products(session, limit=20)
    if not products:
        await _plain_answer(message, "Товары пока не найдены.")
        return
    lines = ["Последние товары:"]
    for product in products:
        status_text = "включен" if product["is_active"] else "выключен"
        default_pack = product["default_pack_size"]["label"]
        lines.append(f"{product['id']}. {product['name']} • {default_pack} • {format_money(product['price'])} • {status_text}")
    await _plain_answer(message, "\n".join(lines))


@router.message(Command("admin_promotions"))
async def admin_promotions_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    async with AsyncSessionLocal() as session:
        promotions = await list_promotions(session, limit=10)
    if not promotions:
        await _plain_answer(message, "Акций пока нет.")
        return
    lines = ["Акции магазина:"]
    for promotion in promotions:
        scope = "весь каталог" if promotion.is_sitewide else "часть товаров"
        status_text = "включена" if promotion.is_active else "отключена"
        value_text = f"{promotion.discount_value}% " if promotion.discount_type == "percent" else f"{format_money(promotion.discount_value)} "
        lines.append(f"{promotion.id}. {promotion.title} • {scope} • {value_text}• {status_text}")
    await _plain_answer(message, "\n".join(lines))


@router.message(Command("admin_promo_codes"))
async def admin_promo_codes_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    async with AsyncSessionLocal() as session:
        promo_codes = await list_promo_codes(session, limit=10)
    if not promo_codes:
        await _plain_answer(message, "Промокодов пока нет.")
        return
    lines = ["Промокоды:"]
    for promo_code in promo_codes:
        status_text = "включен" if promo_code.is_active else "отключен"
        value_text = f"{promo_code.discount_value}% " if promo_code.discount_type == "percent" else f"{format_money(promo_code.discount_value)} "
        lines.append(
            f"{promo_code.id}. {promo_code.code} • {value_text}• использован {promo_code.times_used} раз • {status_text}"
        )
    await _plain_answer(message, "\n".join(lines))


@router.message(Command("admin_tickets"))
async def admin_tickets_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    async with AsyncSessionLocal() as session:
        tickets = await list_payment_tickets(session, limit=10)
    if not tickets:
        await _plain_answer(message, "Тикетов оплаты пока нет.")
        return
    lines = ["Тикеты оплаты:"]
    for ticket in tickets:
        item = serialize_admin_payment_ticket(ticket)
        lines.append(
            f"#{item['id']} • заказ #{item['order_id']} • {item['customer_name']} • "
            f"{format_money(item['payment_amount'])} • {item['status']}"
        )
    await _plain_answer(message, "\n".join(lines))


@router.message(Command("admin_toggle"))
async def admin_toggle_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await _plain_answer(message, "Использование: /admin_toggle (id товара)")
        return
    product_id = int(parts[1])
    async with AsyncSessionLocal() as session:
        product = await toggle_product_active(session, product_id)
    if product is None:
        await _plain_answer(message, "Товар с таким id не найден.")
        return
    status_text = "включен" if product.is_active else "выключен"
    await _plain_answer(message, f"Товар «{product.name}» {status_text}.")


@router.message(Command("admin_publish_product"))
async def admin_publish_product_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await _plain_answer(message, "Использование: /admin_publish_product (id товара)")
        return
    product_id = int(parts[1])
    async with AsyncSessionLocal() as session:
        post = await publish_product_post(session, settings, product_id)
    if post is None:
        await _plain_answer(message, "Товар с таким id не найден.")
        return
    await _plain_answer(
        message,
        f"Товар отправлен в канал {settings.channel_chat_id}.\nПост #{post.id}, message_id={post.message_id}."
    )


@router.message(Command("admin_publish_promotion"))
async def admin_publish_promotion_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await _plain_answer(message, "Использование: /admin_publish_promotion (id акции)")
        return
    promotion_id = int(parts[1])
    async with AsyncSessionLocal() as session:
        post = await publish_promotion_post(session, settings, promotion_id)
    if post is None:
        await _plain_answer(message, "Акция с таким id не найдена.")
        return
    await _plain_answer(
        message,
        f"Акция отправлена в канал {settings.channel_chat_id}.\nПост #{post.id}, message_id={post.message_id}."
    )


@router.message(Command("admin_ticket_confirm"))
async def admin_ticket_confirm_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await _plain_answer(message, "Использование: /admin_ticket_confirm (id тикета)")
        return
    ticket_id = int(parts[1])
    async with AsyncSessionLocal() as session:
        ticket = await confirm_payment_ticket(session, ticket_id)
    if ticket is None:
        await _plain_answer(message, "Тикет с таким id не найден.")
        return
    item = serialize_admin_payment_ticket(ticket)
    await _plain_answer(
        message,
        f"Тикет #{item['id']} подтвержден. Заказ #{item['order_id']} переведен в статус confirmed."
    )


@router.message(Command("admin_ticket_reject"))
async def admin_ticket_reject_handler(message: Message) -> None:
    if await _reject_non_admin(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await _plain_answer(message, "Использование: /admin_ticket_reject (id тикета)")
        return
    ticket_id = int(parts[1])
    async with AsyncSessionLocal() as session:
        ticket = await reject_payment_ticket(session, ticket_id)
    if ticket is None:
        await _plain_answer(message, "Тикет с таким id не найден.")
        return
    item = serialize_admin_payment_ticket(ticket)
    await _plain_answer(
        message,
        f"Тикет #{item['id']} отклонен. Заказ #{item['order_id']} переведен в статус cancelled."
    )
