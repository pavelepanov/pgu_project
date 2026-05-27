# HealthQuest

HealthQuest — учебный MVP фитнес-трекера в формате Telegram Mini App. В первой версии есть профиль Telegram-пользователя, XP и уровни, дневник питания с ручным выбором продуктов, расчет КБЖУ, тренировки, подходы и личные рекорды.

В MVP нет распознавания еды по фото и AI-интеграций. Начальные продукты, упражнения и правила XP создаются Alembic-миграцией.

## Стек

- Backend: Python 3.10+, FastAPI, SQLAlchemy, Alembic, PostgreSQL.
- Bot: aiogram.
- Frontend: React + JavaScript + Vite, без TypeScript.
- Production: Docker Compose, Caddy, HTTPS.

## Локальный запуск

Скопируйте пример окружения:

    cp .env.example .env

В `.env` для локального запуска можно оставить значения PostgreSQL по умолчанию. `BOT_TOKEN` понадобится только для запуска Telegram-бота.

Поднимите PostgreSQL:

    docker compose up -d postgres

Подготовьте backend:

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    alembic upgrade head
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Проверка:

    curl http://localhost:8000/health

Ожидаемый ответ:

    {"status":"ok"}

Подготовьте frontend. Нужен Node.js LTS и npm:

    cd frontend
    npm install
    npm run dev

Откройте:

    http://localhost:5173

В браузере вне Telegram приложение работает в dev-режиме и отправляет заголовок `X-Dev-User: true`.

## Запуск как Telegram Mini App

1. Создайте бота через BotFather и вставьте токен в `.env` как `BOT_TOKEN`.

2. Запустите backend и frontend локально.

3. Сделайте HTTPS-туннель до frontend через localhost.run (в отдельном терминале):

       ssh -R 80:localhost:5173 localhost.run

   Скопируйте полученный URL (например `https://abcd1234.localhost.run`) и вставьте в `.env`:

       WEBAPP_URL=https://abcd1234.localhost.run
       BOT_MODE=polling

4. Запустите бота локально (в отдельном терминале):

       cd backend
       source .venv/bin/activate
       python3 -m app.bot.main

5. Запустите frontend (в отдельном терминале):

       cd frontend
       npm run dev

6. Напишите боту `/start` и нажмите кнопку `Открыть HealthQuest`.

Для локальной разработки используется long polling через SSH-туннель localhost.run: это проще всего и не требует регистрации. Для VPS лучше webhook, потому что сервер уже будет иметь домен и HTTPS.

## Production на VPS

В `.env` укажите реальные значения:

    APP_ENV=production
    DOMAIN=healthquest.example.com
    POSTGRES_USER=healthquest
    POSTGRES_PASSWORD=strong-password
    POSTGRES_DB=healthquest
    BOT_TOKEN=real-telegram-token
    WEBHOOK_SECRET=random-long-secret

Запуск:

    docker compose -f docker-compose.prod.yml up -d --build

Backend в production compose сам выполняет:

    alembic upgrade head

Проверка:

    curl https://healthquest.example.com/health

Для production рекомендуется webhook: Caddy принимает HTTPS, `/bot/webhook` проксируется в FastAPI, а Telegram отправляет обновления на сервер. Если срочно нужно проверить бота на VPS, можно временно оставить polling отдельным процессом, но финальная схема для сервера — webhook.

## Основные API

- `GET /health` — проверка backend.
- `GET /api/profile` — профиль, XP, уровень и рекорды.
- `GET /api/dictionaries/foods?query=...` — продукты.
- `POST /api/nutrition/entries` — добавить прием пищи.
- `GET /api/nutrition/today` — дневник питания за сегодня.
- `GET /api/dictionaries/exercises?query=...` — упражнения.
- `POST /api/workouts` — создать тренировку.
- `POST /api/workouts/{workout_id}/sets` — добавить подход.
- `GET /api/workouts/today` — тренировки за сегодня.

Защищенные endpoints ждут `X-Telegram-Init-Data`. В local-режиме можно использовать `X-Dev-User: true`.
