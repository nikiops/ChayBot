# Чайная Лавка MVP

MVP Telegram-магазина китайского чая в формате:

- Telegram Bot
- Telegram Mini App
- FastAPI Backend API
- PostgreSQL / SQLite fallback
- Docker Compose

## Архитектура

Проект разделён на три независимых, но связанных слоя:

- `backend` хранит бизнес-логику, API, модели БД, миграции, seed-данные, расчёт цен, промокоды и публикацию в канал.
- `bot` живёт внутри backend-кода как отдельный процесс на `aiogram 3`: открывает Mini App, обрабатывает deep links и admin-команды.
- `frontend` представляет собой Telegram Mini App на `React + TypeScript + Vite + Tailwind`, включая витрину и встроенную admin-page.

Поток данных:

1. Пользователь заходит в Telegram-бота.
2. Бот открывает Mini App через `WebApp`-кнопку или deep link.
3. Mini App отправляет Telegram `initData` в backend.
4. Backend валидирует подпись, создаёт или обновляет пользователя, отдаёт каталог, фасовки, корзину, избранное и заказы.
5. После оформления заказа backend сохраняет заказ, применяет промокод и шлёт уведомление админу через Telegram Bot API.
6. Администратор может публиковать товары и акции в канал `-1003357674923` через bot-команды или admin API.

## Структура проекта

```text
backend/
  app/
    api/
    bot/
    core/
    db/
    models/
    schemas/
    services/
    utils/
    main.py
  alembic/
  requirements.txt
  Dockerfile
frontend/
  src/
    app/
    components/
    pages/
    store/
    types/
    utils/
    main.tsx
  package.json
  Dockerfile
docker-compose.yml
.env.example
README.md
start_chaybot.bat
```

## Сущности БД

- `users`
- `categories`
- `products`
- `product_pack_sizes`
- `favorites`
- `cart_items`
- `orders`
- `order_items`
- `promotions`
- `promotion_products`
- `promo_codes`
- `promo_code_products`
- `channel_posts`
- `admin_settings`

## Что есть в MVP

### Bot

- `/start` с приветствием и меню
- кнопки `Открыть магазин`, `Категории`, `Корзина`, `О нас`, `Контакты`
- deep links: `/start`, `/start category_puer`, `/start cart`, `/start promo_discount`
- admin-команды:
  - `/admin`
  - `/admin_stats`
  - `/admin_orders`
  - `/admin_products`
  - `/admin_promotions`
  - `/admin_promo_codes`
  - `/admin_toggle <product_id>`
  - `/admin_publish_product <product_id>`
  - `/admin_publish_promotion <promotion_id>`

### Mini App

- главная страница с баннером, поиском и подборками
- каталог категорий
- список товаров с фильтрами и сортировкой
- карточка товара с выбором фасовки `50 г / 100 г / 250 г` или `1 шт.`
- корзина с промокодом и пересчётом скидки
- checkout
- избранное
- страницы `О нас` и `Контакты`
- экран заказа после оформления
- встроенная страница `/admin` для базового управления магазином

### Backend API

- `GET /api/health`
- `GET /api/categories`
- `GET /api/categories/{slug}`
- `GET /api/products`
- `GET /api/products/featured`
- `GET /api/products/search?q=`
- `GET /api/products/{slug}`
- `GET /api/favorites`
- `POST /api/favorites/toggle`
- `GET /api/cart`
- `POST /api/cart/add`
- `POST /api/cart/update`
- `POST /api/cart/remove`
- `POST /api/orders/create`
- `GET /api/orders/{id}`
- `GET /api/admin/stats`
- `GET /api/admin/orders`
- `GET /api/admin/products`
- `POST /api/admin/products/{id}/toggle`
- `GET /api/admin/promotions`
- `POST /api/admin/promotions`
- `POST /api/admin/promotions/{id}/toggle`
- `GET /api/admin/promo-codes`
- `POST /api/admin/promo-codes`
- `POST /api/admin/promo-codes/{id}/toggle`
- `GET /api/admin/channel/posts`
- `POST /api/admin/channel/products/{id}/publish`
- `POST /api/admin/channel/promotions/{id}/publish`

## Seed-данные

После запуска загружаются:

- 9 категорий
- 20 товаров
- фасовки для чайных позиций и штучные форматы для наборов и посуды
- 2 акции
- 2 промокода
- базовые `admin_settings`

Категории включают: пуэр, улун, зелёный чай, чёрный чай, белый чай, фруктовый чай, наборы, посуду и скидки.

## Локальный запуск

1. Создайте `.env` на основе `.env.example`.
2. Укажите `BOT_TOKEN`, `BOT_USERNAME`, `BOT_ADMIN_IDS` и при необходимости `CHANNEL_CHAT_ID`.
3. Запустите:

```bash
docker-compose up --build
```

Или локально через батник:

```bat
start_chaybot.bat
```

После запуска будут доступны:

- Backend API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Mini App dev server: `http://localhost:5173`

## Подключение Telegram

1. Создайте тестового бота через `@BotFather`.
2. Укажите `BOT_TOKEN`, `BOT_USERNAME` и `BOT_ADMIN_IDS` в `.env`.
3. Добавьте бота администратором в канал `-1003357674923` или замените `CHANNEL_CHAT_ID` на свой.
4. Для Mini App нужен публичный HTTPS-адрес. В проекте уже предусмотрен режим с `ngrok`.

## Deep links для канала

Для продвижения из Telegram-канала можно использовать такие сценарии:

- открыть магазин
- открыть корзину
- открыть категорию
- открыть товар
- открыть акцию

В проекте добавлен helper: `backend/app/utils/deeplinks.py`.

## Авторизация Mini App

- Основной сценарий: backend валидирует `Telegram.WebApp.initData`.
- Для локальной разработки оставлен fallback через demo user (`ALLOW_DEMO_AUTH=true`).
- Для admin API используется тот же механизм плюс проверка `BOT_ADMIN_IDS`.

## Дальнейшее расширение

Каркас уже подготовлен под:

- платежи
- доставку
- бонусы
- расширенную веб-админку
- расписание публикаций в канал
- редактирование существующих постов с медиаконтентом
