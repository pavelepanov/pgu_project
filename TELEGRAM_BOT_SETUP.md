# 🤖 Запуск HealthQuest Bot в Telegram

## Что было добавлено:
✅ Расширение профиля пользователя (рост, вес, возраст, цели)  
✅ Таблица для отслеживания сна и воды (`daily_tracking`)  
✅ Исправление ошибки с отображением беговой дорожки в статистике (кг вместо км)  
✅ Поддержка удаления еды и упражнений с откатом XP  
✅ Готовые планы тренировок уже в БД  

## 📋 Пошаговые инструкции запуска бота

### Шаг 1: Установить зависимости (если еще не установлены)
```bash
cd backend
pip install -r requirements.txt
```

### Шаг 2: Применить миграции БД
```bash
cd backend
alembic upgrade head
```

### Шаг 3: Запустить Backend (в отдельном терминале)
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Шаг 4: Установить ngrok для HTTPS туннеля
```bash
# Windows
choco install ngrok
# или
scoop install ngrok

# macOS
brew install ngrok

# Linux
sudo snap install ngrok
```

### Шаг 4.1: Авторизовать ngrok
Если вы используете ngrok 3, выполните вход одним из способов:
```bash
ngrok login
```
или если у вас токен:
```bash
ngrok config add-authtoken <your-token>
```

### Шаг 5: Запустить ngrok (в отдельном терминале)
```bash
ngrok http 8000
```

Скопируй публичный URL, например `https://abcd1234.ngrok.io`, и добавь в `.env`:
```env
WEBAPP_URL=https://abcd1234.ngrok.io
WEBHOOK_BASE_URL=https://abcd1234.ngrok.io
BOT_MODE=webhook
```

### Шаг 6: Запустить Bot в нужном режиме
Если хочешь работать через webhook и ngrok:
```bash
cd backend
# Просто запусти FastAPI, webhook будет зарегистрирован автоматически
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Если хочешь тестировать локально через polling (без webhook):
```bash
cd backend
python -m app.bot.main
```

### Шаг 6: Запустить Frontend (в отдельном терминале, новый терминал)
```bash
cd frontend
npm run dev
```

Отворится на `http://localhost:5173` для локального тестирования.

## 🎮 Как тестировать в Telegram

1. **Открыть Telegram** и найди своего бота (используй BOT_TOKEN из `.env`)
2. **Отправь `/start`** боту
3. **Нажми на кнопку "Открыть HealthQuest"**
4. **Приложение откроется в Telegram Mini App**, работая через туннель localhost.run

## 🔑 Ключевые переменные в `.env`

| Переменная | Описание |
|-----------|----------|
| `BOT_TOKEN` | Токен Telegram бота (получишь у BotFather) |
| `WEBAPP_URL` | HTTPS URL туннеля (localhost.run) для Mini App |
| `DATABASE_URL` | PostgreSQL строка подключения |
| `APP_ENV` | `local` или `production` |
| `BOT_MODE` | `polling` (локально, рекомендуется) или `webhook` (production) |

## 📱 Функции, готовые к тестированию

- ✅ Регистрация через Telegram
- ✅ Добавление еды и расчет БЖУ
- ✅ Создание тренировок и планов
- ✅ Просмотр личных рекордов
- ✅ Статистика за период
- ✅ Система XP и уровней
- ✅ Поддержка кардио (км, мин, км/ч, темп)

## 🚀 Следующие шаги

После запуска бота:
1. Исправить отображение кардио в UI статистики
2. Добавить удаления еды/упражнений с откатом XP
3. Интегрировать g4f для AI-сводки дня
4. Добавить ввод профиля пользователя (рост, вес, возраст)
5. Добавить выбор целей и расчет БЖУ норм

## 🐛 Если что-то не работает

**Проблема: "BOT_TOKEN not valid"**
→ Получи новый от @BotFather в Telegram

**Проблема: "Cannot connect to database"**
→ Проверь PostgreSQL запущен и DATABASE_URL в `.env`

**Проблема: "Mini App не открывается"**
→ Проверь:
  - WEBAPP_URL начинается с `https://`
  - localhost.run туннель активен (окно остается открытым)
  - Бота перезапустил после смены WEBAPP_URL
  - Frontend доступен по URL из туннеля (открой в браузере)

**Проблема: "Port 8000 already in use"**
→ Убей процесс: `lsof -ti:8000 | xargs kill -9` (Unix) или используй другой порт

---

**Создано:** 2026-05-21  
**Версия:** 0.1.0  
**Статус:** MVP готов к тестированию в Telegram
