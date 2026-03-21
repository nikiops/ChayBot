import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.admin_setting import AdminSetting
from app.models.category import Category
from app.models.product_pack_size import ProductPackSize
from app.models.promo_code import PromoCode
from app.models.product import Product
from app.models.promotion import Promotion
from app.db.seeds.catalog import ADMIN_SETTINGS, CATEGORIES, PRODUCTS
from app.db.seeds.marketing import PROMO_CODES, PROMOTIONS

TEA_CATEGORY_SLUGS = {"puer", "oolong", "green-tea", "black-tea", "white-tea", "fruit-tea"}


def _to_sum_price(value: str | None) -> Decimal | None:
    if value is None:
        return None
    return (Decimal(value) * Decimal("100")).quantize(Decimal("0.01"))


def _scaled_price(value: Decimal | None, factor: str) -> Decimal | None:
    if value is None:
        return None
    return (value * Decimal(factor)).quantize(Decimal("0.01"))


async def seed_categories() -> dict[str, Category]:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Category))
        categories_by_slug = {category.slug: category for category in existing.scalars().all()}

        for item in CATEGORIES:
            category = categories_by_slug.get(item["slug"])
            if category is None:
                category = Category(**item, is_active=True)
                session.add(category)
                await session.flush()
                categories_by_slug[category.slug] = category
            else:
                category.name = item["name"]
                category.description = item["description"]
                category.image_url = item["image_url"]
                category.sort_order = item["sort_order"]
                category.is_active = True

        await session.commit()
        return categories_by_slug


async def seed_products(categories_by_slug: dict[str, Category]) -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Product))
        products_by_slug = {product.slug: product for product in existing.scalars().all()}

        for item in PRODUCTS:
            category = categories_by_slug[item["category_slug"]]
            payload = {
                "category_id": category.id,
                "name": item["name"],
                "slug": item["slug"],
                "short_description": item["short_description"],
                "full_description": item["full_description"],
                "price": _to_sum_price(item["price"]),
                "old_price": _to_sum_price(item["old_price"]),
                "image_url": item["image_url"],
                "stock_qty": item["stock_qty"],
                "is_active": True,
                "is_featured": item["is_featured"],
            }
            product = products_by_slug.get(item["slug"])
            if product is None:
                session.add(Product(**payload))
            else:
                for key, value in payload.items():
                    setattr(product, key, value)

        await session.commit()


def _build_pack_payloads(product: Product, category_slug: str) -> list[dict]:
    if category_slug in TEA_CATEGORY_SLUGS:
        return [
            {
                "label": "50 г",
                "weight_grams": 50,
                "price": _scaled_price(product.price, "0.62"),
                "old_price": _scaled_price(product.old_price, "0.62"),
                "stock_qty": max(4, product.stock_qty + 4),
                "sort_order": 1,
                "is_default": False,
            },
            {
                "label": "100 г",
                "weight_grams": 100,
                "price": product.price,
                "old_price": product.old_price,
                "stock_qty": product.stock_qty,
                "sort_order": 2,
                "is_default": True,
            },
            {
                "label": "250 г",
                "weight_grams": 250,
                "price": _scaled_price(product.price, "2.35"),
                "old_price": _scaled_price(product.old_price, "2.35"),
                "stock_qty": max(2, product.stock_qty // 2 + 2),
                "sort_order": 3,
                "is_default": False,
            },
        ]

    return [
        {
            "label": "1 шт.",
            "weight_grams": None,
            "price": product.price,
            "old_price": product.old_price,
            "stock_qty": product.stock_qty,
            "sort_order": 1,
            "is_default": True,
        }
    ]


async def seed_pack_sizes() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).options(selectinload(Product.category)))
        products = list(result.scalars().all())
        existing = await session.execute(select(ProductPackSize))
        pack_sizes_by_product: dict[int, dict[str, ProductPackSize]] = {}
        for pack_size in existing.scalars().all():
            pack_sizes_by_product.setdefault(pack_size.product_id, {})[pack_size.label] = pack_size

        for product in products:
            desired = _build_pack_payloads(product, product.category.slug)
            existing_for_product = pack_sizes_by_product.get(product.id, {})
            desired_labels = {item["label"] for item in desired}

            for payload in desired:
                pack_size = existing_for_product.get(payload["label"])
                if pack_size is None:
                    session.add(ProductPackSize(product_id=product.id, **payload))
                    continue
                for key, value in payload.items():
                    setattr(pack_size, key, value)

            for label, pack_size in existing_for_product.items():
                if label not in desired_labels:
                    await session.delete(pack_size)

        await session.commit()


async def seed_admin_settings() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(AdminSetting))
        settings_by_key = {setting.key: setting for setting in existing.scalars().all()}
        for item in ADMIN_SETTINGS:
            setting = settings_by_key.get(item["key"])
            if setting is None:
                session.add(AdminSetting(**item))
            else:
                setting.value = item["value"]
        await session.commit()


async def seed_promotions() -> None:
    async with AsyncSessionLocal() as session:
        products = await session.execute(select(Product))
        products_by_slug = {product.slug: product for product in products.scalars().all()}
        existing = await session.execute(select(Promotion).options(selectinload(Promotion.products)))
        promotions_by_slug = {promotion.slug: promotion for promotion in existing.scalars().all()}

        for item in PROMOTIONS:
            promotion = promotions_by_slug.get(item["slug"])
            payload = {
                "title": item["title"],
                "slug": item["slug"],
                "description": item["description"],
                "image_url": item["image_url"],
                "badge_text": item["badge_text"],
                "discount_type": item["discount_type"],
                "discount_value": Decimal(item["discount_value"]),
                "is_sitewide": item["is_sitewide"],
                "is_active": item["is_active"],
            }
            if promotion is None:
                promotion = Promotion(**payload)
                session.add(promotion)
            else:
                for key, value in payload.items():
                    setattr(promotion, key, value)

            promotion.products = [products_by_slug[slug] for slug in item["product_slugs"] if slug in products_by_slug]

        await session.commit()


async def seed_promo_codes() -> None:
    async with AsyncSessionLocal() as session:
        products = await session.execute(select(Product))
        products_by_slug = {product.slug: product for product in products.scalars().all()}
        existing = await session.execute(select(PromoCode).options(selectinload(PromoCode.products)))
        promo_codes_by_code = {promo_code.code: promo_code for promo_code in existing.scalars().all()}

        for item in PROMO_CODES:
            normalized_code = item["code"].strip().upper()
            promo_code = promo_codes_by_code.get(normalized_code)
            payload = {
                "code": normalized_code,
                "title": item["title"],
                "description": item["description"],
                "discount_type": item["discount_type"],
                "discount_value": Decimal(item["discount_value"]),
                "is_sitewide": item["is_sitewide"],
                "minimum_order_amount": Decimal(item["minimum_order_amount"]) if item["minimum_order_amount"] else None,
                "max_uses": item["max_uses"],
                "is_active": item["is_active"],
            }
            if promo_code is None:
                promo_code = PromoCode(**payload)
                session.add(promo_code)
            else:
                for key, value in payload.items():
                    setattr(promo_code, key, value)

            promo_code.products = [products_by_slug[slug] for slug in item["product_slugs"] if slug in products_by_slug]

        await session.commit()


async def main() -> None:
    settings = get_settings()
    categories_by_slug = await seed_categories()
    await seed_products(categories_by_slug)
    await seed_pack_sizes()
    await seed_promotions()
    await seed_promo_codes()
    await seed_admin_settings()
    print(f"Seed completed for {settings.app_name}.")


if __name__ == "__main__":
    asyncio.run(main())
