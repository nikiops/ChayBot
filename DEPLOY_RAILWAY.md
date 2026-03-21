# Railway Deploy

Проект подготовлен под деплой из GitHub в Railway как монорепа с тремя сервисами:

1. `goldentea-api`
2. `goldentea-bot`
3. `goldentea-web`

## Структура сервисов

### 1. Backend API

- `Root Directory`: `backend`
- Dockerfile: стандартный `backend/Dockerfile`
- Healthcheck path: `/api/health`
- Публичный домен: рекомендуется `api.goldentea.uz`

Переменные:

- `DATABASE_URL` от Railway PostgreSQL
- `MEDIA_DIR=/app/media`
- `ENVIRONMENT=production`
- `DEBUG=false`
- `BOT_TOKEN`
- `BOT_USERNAME`
- `BOT_ADMIN_IDS`
- `FRONTEND_APP_URL=https://goldentea.uz`
- `BACKEND_PUBLIC_URL=https://api.goldentea.uz`
- `CORS_ORIGINS=https://goldentea.uz,https://www.goldentea.uz,https://api.goldentea.uz`
- `ALLOW_DEMO_AUTH=false`
- `USE_NGROK_FOR_WEBAPP=false`
- `CHANNEL_CHAT_ID=-1003357674923`

### 2. Bot worker

- `Root Directory`: `backend`
- `RAILWAY_DOCKERFILE_PATH=Dockerfile.bot`
- домен не нужен

Переменные:

- те же, что и у API
- `DATABASE_URL` должен указывать на ту же PostgreSQL базу

### 3. Mini App frontend

- `Root Directory`: `frontend`
- Dockerfile: стандартный `frontend/Dockerfile`
- Кастомный домен: `goldentea.uz`

Переменные:

- `VITE_API_URL=https://api.goldentea.uz/api`
- `VITE_DEMO_USER_ID=900000001`

## Домен `goldentea.uz`

Для фронтенда используйте кастомный домен `goldentea.uz`.

Рекомендуемая схема:

- `goldentea.uz` -> Railway frontend service
- `api.goldentea.uz` -> Railway backend service

## Скриншоты оплаты

У проекта есть тикетная оплата со скриншотами чеков. Эти файлы сохраняются в локальную папку `media`,
поэтому для production у `goldentea-api` нужно подключить Railway Volume и смонтировать его в `/app/media`.

Если DNS управляется через Cloudflare:

- добавьте `CNAME` для `@` на значение Railway, которое покажет сервис
- добавьте `CNAME` для `www` на `@`
- в Cloudflare выставьте `SSL/TLS = Full`

## Telegram Mini App

После деплоя:

1. В `@BotFather` укажите Web App URL: `https://goldentea.uz`
2. Убедитесь, что `BOT_USERNAME` совпадает с реальным username бота
3. Добавьте бота админом в канал
4. Проверьте, что backend домен доступен по `https://api.goldentea.uz/api/health`

## Seed и миграции

API-контейнер автоматически применяет Alembic миграции при старте.

Seed-данные не запускаются автоматически, чтобы не перетирать production.
Если нужен первичный контент:

```bash
python -m app.db.seed
```

Эту команду лучше выполнить один раз вручную через Railway shell/run command.

## Что уже учтено в коде

- frontend читает `VITE_API_URL` через runtime-config, поэтому домен API можно менять без пересборки исходников
- backend и bot готовы работать от Railway `DATABASE_URL`
- Mini App URL берется из `FRONTEND_APP_URL`, поэтому в production бот будет открывать `https://goldentea.uz`
- ngrok для production отключается через `USE_NGROK_FOR_WEBAPP=false`
