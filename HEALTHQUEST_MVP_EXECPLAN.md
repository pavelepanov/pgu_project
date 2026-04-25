# Реализация MVP Telegram Mini App HealthQuest

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

Этот файл должен поддерживаться в соответствии с `PLANS.md` из корня репозитория. Важное исключение для этого проекта: пользователь строго запретил использовать git, поэтому в этом плане нет команд `git`, коммитов и любых действий с историей репозитория.

## Purpose / Big Picture

После выполнения этого плана у команды будет простая первая версия HealthQuest: Telegram Mini App, в котором пользователь входит через Telegram, видит профиль, уровень и XP, ведет дневник питания, добавляет тренировочные подходы и смотрит личные рекорды. MVP не распознает еду по фото и не интегрируется с AI: питание добавляется вручную из заранее заполненной базы продуктов.

Проверить результат можно будет без специальных знаний: запустить PostgreSQL, применить Alembic-миграции с начальными продуктами и упражнениями, поднять FastAPI backend, открыть React Mini App через Telegram-бота и вручную добавить прием пищи или тренировочный подход. После этого на главном экране должны измениться калории, БЖУ, XP, уровень и личные рекорды.

## Progress

- [x] (2026-04-25 08:49Z) Проанализировано ТЗ проекта HealthQuest и ограничения пользователя: FastAPI, PostgreSQL, React без TypeScript, без AI-фото в MVP, без автоматических тестов, без сложной архитектуры, без git.
- [x] (2026-04-25 08:49Z) Создан этот самодостаточный ExecPlan для реализации MVP.
- [x] (2026-04-25 09:06Z) Создана структура backend в `backend/`.
- [x] (2026-04-25 09:06Z) Создана структура frontend в `frontend/`.
- [x] (2026-04-25 09:06Z) Добавлен Docker Compose для PostgreSQL и удобного локального запуска.
- [x] (2026-04-25 09:06Z) Добавлена Alembic-миграция: схема БД и seed-данные продуктов, упражнений и правил XP.
- [x] (2026-04-25 09:06Z) Реализован FastAPI API для профиля, питания, тренировок, XP и рекордов.
- [x] (2026-04-25 09:06Z) Реализован простой Telegram-бот на aiogram с кнопкой открытия Mini App, polling для local и webhook endpoint для production.
- [x] (2026-04-25 09:06Z) Реализован React-интерфейс в стиле Apple: легкий, чистый, мобильный, без копирования Apple один в один.
- [x] (2026-04-25 09:06Z) Подготовлены инструкции локального запуска Mini App через HTTPS-туннель.
- [x] (2026-04-25 09:06Z) Подготовлены инструкции запуска на VPS через Docker Compose и HTTPS.
- [ ] Провести ручную приемку MVP по сценариям из раздела `Validation and Acceptance` после установки Python-зависимостей и Node.js LTS.

## Surprises & Discoveries

- Observation: В репозитории на момент составления плана есть только `README.md` и `PLANS.md`.
  Evidence: Команда `rg --files` из `/home/pavel/pgu_project` вывела `README.md` и `PLANS.md`.

- Observation: В окружении доступен `python3`, но команды `python`, `node` и `npm` отсутствуют.
  Evidence: `python --version` вернул `command not found`, `python3 --version` вернул `Python 3.13.7`, `npm --version` вернул `command not found`.

- Observation: Backend-файлы синтаксически корректны на уровне Python-компиляции.
  Evidence: `python3 -m compileall backend/app backend/alembic` успешно скомпилировал все Python-файлы.

- Observation: Полный локальный запуск в текущем окружении заблокирован системными зависимостями.
  Evidence: `python3 -c "import fastapi, sqlalchemy, alembic"` вернул `ModuleNotFoundError: No module named 'fastapi'`, `npm --version` вернул `command not found`, `docker image ls` вернул `permission denied while trying to connect to the docker API`.

## Decision Log

- Decision: Первая версия HealthQuest не реализует распознавание еды по фото, загрузку фотографий и AI-интеграции.
  Rationale: Пользователь прямо попросил отказаться от AI-фото в MVP. Это уменьшает риск, ускоряет учебную реализацию и оставляет понятный ручной сценарий: поиск продукта, граммовка, расчет КБЖУ.
  Date/Author: 2026-04-25 / Codex

- Decision: Backend делать на FastAPI без сложной архитектуры: `models.py`, `schemas.py`, `crud.py`, `auth.py`, `main.py` и небольшие роутеры.
  Rationale: Для вузовского MVP важнее быстро получить работающий продукт, чем поддерживать много слоев абстракций. Такой подход легко читать новичкам и достаточно хорошо расширяется для текущего ТЗ.
  Date/Author: 2026-04-25 / Codex

- Decision: Frontend делать на JavaScript + React + Vite без TypeScript.
  Rationale: Пользователь прямо указал React без TS. Vite дает самый простой старт и быструю сборку.
  Date/Author: 2026-04-25 / Codex

- Decision: Telegram initData проверять на backend при каждом защищенном запросе через заголовок `X-Telegram-Init-Data`; отдельные пароли и JWT для MVP не добавлять.
  Rationale: Telegram Mini App уже передает подписанные данные запуска. Проверка initData на сервере соответствует ТЗ и проще, чем вводить отдельную систему сессий.
  Date/Author: 2026-04-25 / Codex

- Decision: Для бота предусмотреть два режима: локально `long polling`, на VPS предпочтительно `webhook`.
  Rationale: Long polling проще для разработки, потому что не требует публичного HTTPS-адреса для приема событий от Telegram. На сервере webhook удобнее и привычнее для деплоя: Telegram сам отправляет обновления на HTTPS endpoint, а процесс бота не держит постоянный polling-цикл. Так как Mini App на реальном сервере все равно требует HTTPS-домен, webhook хорошо ложится на production-схему.
  Date/Author: 2026-04-25 / Codex

- Decision: Начальные продукты, упражнения, группы мышц и правила начисления XP создавать через seed-миграцию Alembic.
  Rationale: Пользователь попросил именно seed-миграцию. Это делает начальное состояние БД воспроизводимым на локальной машине и на VPS.
  Date/Author: 2026-04-25 / Codex

- Decision: Автоматические тесты не писать, но оставить ручные проверки, healthcheck, Swagger UI и curl-сценарии.
  Rationale: Пользователь прямо сказал, что тесты писать не нужно. При этом MVP должен быть проверяемым, поэтому приемка будет ручной и наблюдаемой.
  Date/Author: 2026-04-25 / Codex

- Decision: Не использовать git ни для проверки состояния, ни для коммитов, ни для откатов.
  Rationale: Пользователь строго запретил использовать git. Все инструкции и команды должны работать без обращения к git.
  Date/Author: 2026-04-25 / Codex

## Outcomes & Retrospective

На 2026-04-25 09:06Z реализация MVP создана в коде. Готовы backend, Alembic schema+seed, API, aiogram-бот, React Mini App, Docker Compose, production Caddy-схема и README с запуском. Backend прошел синтаксическую проверку через `python3 -m compileall`.

Полная ручная приемка не выполнена в текущем окружении, потому что здесь нет `node`/`npm`, Python-зависимости проекта не установлены, а доступ к Docker daemon запрещен. Следующий исполнитель должен установить зависимости, применить миграции, поднять backend/frontend и пройти сценарии из `Validation and Acceptance`.

## Context and Orientation

Репозиторий сейчас почти пустой. `README.md` содержит только название проекта, а `PLANS.md` описывает формат таких исполняемых планов. Поэтому реализация должна создать проект с нуля.

HealthQuest по ТЗ — это фитнес-трекер внутри Telegram. Telegram Mini App — это обычное web-приложение, которое открывается во встроенном браузере Telegram. Оно получает от Telegram строку `initData`: в ней есть данные пользователя и подпись. Backend обязан проверить подпись, чтобы убедиться, что пользователь действительно пришел из Telegram, а не подделал запрос.

FastAPI — Python-фреймворк для HTTP API. В этом проекте FastAPI будет отдавать JSON endpoints для профиля, питания, тренировок и статистики. PostgreSQL будет хранить пользователей, продукты, приемы пищи, упражнения, тренировки, подходы, XP и рекорды. Alembic — инструмент миграций: он создает и изменяет таблицы, а также один раз добавляет начальные справочники продуктов и упражнений.

React Mini App будет отдельным frontend-приложением на JavaScript. Оно будет вызывать backend API и отправлять `window.Telegram.WebApp.initData` в заголовке каждого запроса. Если приложение открыто вне Telegram во время локальной разработки, frontend должен показывать аккуратный dev-режим, а backend должен принимать фиксированного dev-пользователя только при `APP_ENV=local`.

Telegram-бот нужен для входа в Mini App и уведомлений. Для MVP достаточно команды `/start`, которая отправляет кнопку открытия приложения. Уведомления о новом уровне можно реализовать как простое сообщение после действий, если есть `telegram_id` пользователя и токен бота.

## Target Repository Structure

Создать следующую простую структуру:

    backend/
      alembic/
        versions/
      app/
        __init__.py
        main.py
        config.py
        db.py
        models.py
        schemas.py
        auth.py
        crud.py
        xp.py
        routers/
          __init__.py
          profile.py
          nutrition.py
          workouts.py
          dictionaries.py
        bot/
          __init__.py
          main.py
      alembic.ini
      requirements.txt
      Dockerfile
    frontend/
      index.html
      package.json
      vite.config.js
      src/
        main.jsx
        App.jsx
        api.js
        telegram.js
        styles.css
        components/
          Shell.jsx
          StatRing.jsx
          IconButton.jsx
        screens/
          TodayScreen.jsx
          NutritionScreen.jsx
          WorkoutScreen.jsx
          ProfileScreen.jsx
    docker-compose.yml
    docker-compose.prod.yml
    .env.example
    README.md
    HEALTHQUEST_MVP_EXECPLAN.md

Если при реализации станет ясно, что какой-то файл лишний, его можно не создавать, но нельзя усложнять структуру без причины. Важнее сохранить простоту: один понятный backend, один понятный frontend, одна база данных.

## MVP Scope

MVP включает авторизацию через Telegram initData, профиль пользователя, уровень и XP, дневник питания, ручной поиск продуктов, расчет калорий и БЖУ за текущий день, список упражнений, создание тренировки, добавление подходов, просмотр предыдущих весов по упражнению, личные рекорды и простого бота с кнопкой открытия приложения.

MVP не включает распознавание еды по фото, хранение фотографий, AI-анализ блюд, сложные цели питания, социальные функции, админ-панель, push-расписания, сложные шаблоны программ тренировок, оплату, полноценные автоматические тесты и сложную clean architecture.

## Backend Plan

Backend должен быть максимально прямым. В `backend/requirements.txt` указать зависимости:

    fastapi
    uvicorn[standard]
    sqlalchemy
    psycopg2-binary
    alembic
    pydantic-settings
    python-dotenv
    aiogram

В `backend/app/config.py` создать настройки через `pydantic-settings`: `APP_ENV`, `DATABASE_URL`, `BOT_TOKEN`, `WEBAPP_URL`, `DEV_TELEGRAM_USER_ID`, `DEV_TELEGRAM_FIRST_NAME`, `CORS_ORIGINS`, `BOT_MODE`, `WEBHOOK_BASE_URL`, `WEBHOOK_SECRET`.

В `backend/app/db.py` создать SQLAlchemy engine, `SessionLocal` и dependency `get_db()`. Для простоты использовать синхронный SQLAlchemy. Это легче для учебного проекта, чем async SQLAlchemy, и хорошо работает с FastAPI для MVP.

В `backend/app/models.py` описать таблицы:

    users:
      telegram_id BigInteger primary key
      first_name String
      last_name String nullable
      username String nullable
      photo_url String nullable
      xp_total Integer default 0
      created_at DateTime
      updated_at DateTime

    food_products:
      id Integer primary key
      name String unique
      brand String nullable
      calories_per_100g Integer
      protein_per_100g Numeric
      fat_per_100g Numeric
      carbs_per_100g Numeric
      default_grams Integer default 100
      is_active Boolean default true

    meal_entries:
      id Integer primary key
      user_telegram_id ForeignKey users.telegram_id
      product_id ForeignKey food_products.id nullable
      meal_type String
      product_name String
      grams Integer
      calories Integer
      protein Numeric
      fat Numeric
      carbs Numeric
      eaten_at DateTime
      created_at DateTime

    exercises:
      id Integer primary key
      name String unique
      load_type String
      muscle_group String
      is_active Boolean default true

    workouts:
      id Integer primary key
      user_telegram_id ForeignKey users.telegram_id
      title String
      performed_at DateTime
      created_at DateTime

    workout_sets:
      id Integer primary key
      workout_id ForeignKey workouts.id
      exercise_id ForeignKey exercises.id
      set_index Integer
      weight_kg Numeric
      reps Integer
      created_at DateTime

    personal_records:
      id Integer primary key
      user_telegram_id ForeignKey users.telegram_id
      exercise_id ForeignKey exercises.id
      max_weight_kg Numeric default 0
      max_reps Integer default 0
      updated_at DateTime

    xp_events:
      id Integer primary key
      user_telegram_id ForeignKey users.telegram_id
      source_type String
      source_id Integer
      xp_amount Integer
      created_at DateTime

Не добавлять отдельные таблицы ролей, прав, refresh token, сессий или аудита. Для MVP это лишнее.

В `backend/app/auth.py` реализовать проверку Telegram initData. Алгоритм: разобрать query string, вынуть `hash`, отсортировать остальные пары `key=value` по ключу, склеить через перенос строки, получить `secret_key = HMAC_SHA256(key="WebAppData", message=BOT_TOKEN)`, затем посчитать `expected_hash = HMAC_SHA256(key=secret_key, message=data_check_string)` и сравнить его с переданным `hash`. Сравнение выполнять через безопасное сравнение, например `hmac.compare_digest`. В production дополнительно проверять `auth_date`: если данные старше 24 часов, возвращать HTTP 401.

В local dev режиме разрешить заголовок `X-Dev-User: true`, только если `APP_ENV=local`. Тогда backend создает пользователя с `DEV_TELEGRAM_USER_ID`. В production этот путь должен быть выключен.

В `backend/app/xp.py` сделать простые правила:

    За добавление приема пищи: 10 XP.
    За каждый тренировочный подход: 5 XP.
    Уровень: level = xp_total // 100 + 1.
    Прогресс до следующего уровня: xp_total % 100 из 100.

Эти правила также записать в seed-миграции как комментарий или в отдельную таблицу `xp_rules`, если захочется показывать их в UI. Для MVP достаточно функции в коде, но seed-миграция должна создать базовые продукты и упражнения.

В `backend/app/crud.py` держать простые функции для работы с БД: upsert пользователя из Telegram, поиск продуктов, создание приема пищи, дневная сводка питания, поиск упражнений, создание тренировки, добавление подхода, обновление личного рекорда, расчет профиля.

В `backend/app/main.py` создать приложение FastAPI, CORS, endpoint `GET /health` и подключить роутеры.

## API Plan

Все защищенные endpoints должны читать пользователя из Telegram initData. Frontend отправляет заголовок:

    X-Telegram-Init-Data: <window.Telegram.WebApp.initData>

Для local dev frontend может отправить:

    X-Dev-User: true

Endpoints:

    GET /health
      Возвращает {"status":"ok"}.

    GET /api/profile
      Возвращает Telegram-профиль, xp_total, level, xp_progress, personal_records.

    GET /api/dictionaries/foods?query=...
      Возвращает продукты из seed-справочника.

    GET /api/dictionaries/exercises?query=...&muscle_group=...
      Возвращает упражнения из seed-справочника.

    GET /api/nutrition/today
      Возвращает приемы пищи за текущий день и суммы calories, protein, fat, carbs.

    POST /api/nutrition/entries
      Принимает product_id, meal_type, grams. Backend пересчитывает КБЖУ по продукту, создает entry и начисляет 10 XP.

    DELETE /api/nutrition/entries/{entry_id}
      Удаляет запись питания. Для простоты XP в MVP можно не откатывать, но это решение нужно отразить в UI: удаление исправляет дневник, а не историю мотивации.

    GET /api/workouts/today
      Возвращает сегодняшние тренировки и подходы.

    POST /api/workouts
      Создает тренировку с title.

    POST /api/workouts/{workout_id}/sets
      Принимает exercise_id, weight_kg, reps. Backend добавляет подход, начисляет 5 XP и обновляет personal_records.

    GET /api/workouts/previous-set?exercise_id=...
      Возвращает последний подход пользователя по этому упражнению до текущего дня.

    GET /api/stats/summary
      Можно добавить позже, если frontend станет проще от отдельной общей сводки. На первом проходе достаточно `/api/profile`, `/api/nutrition/today`, `/api/workouts/today`.

Валидация должна быть простой, но обязательной: grams > 0 и <= 3000, reps > 0 и <= 300, weight_kg >= 0 и <= 500, meal_type только `breakfast`, `lunch`, `dinner`, `snack`.

## Alembic and Seed Data Plan

Сначала инициализировать Alembic в `backend/`. Затем создать первую миграцию, которая создает все таблицы. Следующей миграцией создать seed-данные или объединить схему и seed в одну начальную миграцию. Для учебного MVP проще одна начальная миграция `0001_initial_schema_and_seed.py`.

Seed-данные должны быть идемпотентными: повторный запуск миграции в уже примененной базе обычно не выполняется, но SQL вставки все равно лучше писать с `ON CONFLICT DO NOTHING` для продуктов и упражнений. Это поможет при ручном восстановлении.

Начальные продукты:

    Овсянка, 100 г: 379 ккал, Б 13.2, Ж 6.5, У 67.7
    Куриная грудка, 100 г: 165 ккал, Б 31.0, Ж 3.6, У 0.0
    Рис вареный, 100 г: 130 ккал, Б 2.7, Ж 0.3, У 28.0
    Яйцо куриное, 100 г: 155 ккал, Б 13.0, Ж 11.0, У 1.1
    Творог 5%, 100 г: 121 ккал, Б 17.0, Ж 5.0, У 1.8
    Банан, 100 г: 89 ккал, Б 1.1, Ж 0.3, У 23.0
    Гречка вареная, 100 г: 110 ккал, Б 3.6, Ж 1.1, У 21.3
    Лосось, 100 г: 208 ккал, Б 20.0, Ж 13.0, У 0.0
    Йогурт натуральный, 100 г: 61 ккал, Б 3.5, Ж 3.3, У 4.7
    Салат овощной, 100 г: 45 ккал, Б 1.5, Ж 2.0, У 5.5

Начальные упражнения:

    Жим лежа: силовая, грудь
    Присед со штангой: силовая, ноги
    Становая тяга: силовая, спина
    Тяга верхнего блока: силовая, спина
    Жим гантелей сидя: силовая, плечи
    Подъем штанги на бицепс: силовая, руки
    Разгибание рук на блоке: силовая, руки
    Планка: статическая, корпус
    Беговая дорожка: кардио, все тело
    Велотренажер: кардио, ноги

Если команда хочет добавить больше справочников, делать это отдельной seed-миграцией, а не вручную через базу.

## Frontend Plan

Frontend должен быть реальным приложением, а не лендингом. Первый экран после загрузки — рабочая вкладка `Сегодня`, где пользователь сразу видит калории, БЖУ, XP, уровень и быстрые действия.

Зависимости в `frontend/package.json`:

    @vitejs/plugin-react
    vite
    react
    react-dom
    lucide-react

TypeScript не добавлять. CSS можно сделать обычным `src/styles.css`, без Tailwind и без тяжелой UI-библиотеки. Это проще для команды и понятнее на защите.

В `frontend/src/telegram.js` сделать функции:

    getTelegram()
    getInitData()
    getThemeParams()
    isTelegram()
    expandApp()
    hapticImpact()

Если Telegram SDK недоступен, frontend работает в dev-режиме и показывает маленькую метку `Dev`.

В `frontend/src/api.js` сделать один helper `apiFetch(path, options)`, который добавляет `X-Telegram-Init-Data` или `X-Dev-User`.

Экраны:

    TodayScreen.jsx
      Сводка дня, кольца/полосы калорий и БЖУ, быстрые кнопки "Еда" и "Тренировка", последние записи.

    NutritionScreen.jsx
      Сегментированный выбор завтрак/обед/ужин/перекус, поиск продукта, ввод граммов, расчет preview КБЖУ до сохранения, список сегодняшних приемов пищи.

    WorkoutScreen.jsx
      Создание или выбор сегодняшней тренировки, поиск упражнения, ввод веса и повторений, подсказка предыдущего веса, список подходов.

    ProfileScreen.jsx
      Telegram avatar, имя, уровень, XP progress, личные рекорды.

Навигация — нижняя tab bar с иконками `lucide-react`: Today, Utensils, Dumbbell, User. Текст на кнопках должен быть коротким и не ломаться на узких экранах.

## Design Direction

Дизайн должен быть элегантным и дорогим на вид, в духе современных Apple-интерфейсов, но без прямого копирования Apple. Использовать системный шрифт:

    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;

Визуальный стиль:

    Светлая тема по умолчанию, поддержка Telegram theme params там, где они есть.
    Фон: почти белый `#f5f5f7`, поверхности `#ffffff`, текст `#1d1d1f`.
    Акценты: глубокий синий для действий, зеленый для питания, коралловый или оранжевый для тренировок, без доминирования одного оттенка.
    Радиусы карточек и контролов не больше 8px, чтобы UI выглядел аккуратно и не игрушечно.
    Мягкие hairline borders `rgba(0,0,0,0.08)`, очень легкие тени только для важных поверхностей.
    Крупные цифры для калорий, XP и веса, но компактные заголовки внутри панелей.
    Никаких маркетинговых hero-блоков, декоративных градиентных шаров, лишних описаний функций или инструкций внутри приложения.

Главный принцип: интерфейс должен выглядеть как аккуратный мобильный инструмент для ежедневного использования. Пользователь открывает приложение в Telegram и сразу понимает, что добавить еду или подход можно за несколько касаний.

Состояния, которые обязательно предусмотреть:

    Загрузка данных.
    Пустой дневник питания.
    Пустая тренировка.
    Ошибка сети.
    Неверные данные формы.
    Успешное сохранение с обновлением XP.

## Telegram Mini App Setup

Для локальной разработки проще использовать long polling у бота и HTTPS-туннель для frontend.

1. Создать бота через BotFather и получить `BOT_TOKEN`.

2. Запустить frontend локально на `http://localhost:5173`.

3. Сделать публичный HTTPS URL для frontend через любой туннель. Например:

       cloudflared tunnel --url http://localhost:5173

   или:

       ngrok http 5173

   Важно: Telegram Mini App должен открываться по HTTPS. Обычный `localhost` подходит для браузера разработчика, но не подходит как нормальная ссылка для пользователей в Telegram на телефоне.

4. Записать полученный HTTPS URL в `.env` как `WEBAPP_URL`.

5. Запустить бота в режиме long polling:

       cd /home/pavel/pgu_project/backend
       python3 -m app.bot.main

6. Написать боту `/start`. Бот должен отправить кнопку `Открыть HealthQuest`, которая открывает `WEBAPP_URL`.

Для production на VPS лучше использовать webhooks. Причина: на сервере уже будет домен и HTTPS для Mini App, поэтому bot webhook можно повесить на тот же домен, например `https://healthquest.example.com/bot/webhook`. Telegram будет сам присылать события боту, а не ждать, пока процесс бота их опросит. Это удобнее для будущего деплоя и привычно, если команда уже работала с webhooks.

Итоговое решение:

    Локально: long polling, потому что проще.
    На VPS: webhook, потому что есть HTTPS-домен и это чище для постоянного сервера.

Если сроки будут гореть, на VPS можно временно оставить long polling отдельным Docker-сервисом `bot`. Это будет работать, пока процесс постоянно запущен. Но финальная рекомендуемая схема для защиты и дальнейшего развития — webhook.

## Bot Plan

В `backend/app/bot/main.py` создать aiogram-бота. Для MVP нужны:

    /start
      Отправляет приветствие и кнопку открытия Mini App.

    /help
      Коротко сообщает, что приложение открывается кнопкой.

    webhook endpoint
      Нужен для production-режима. Можно реализовать в FastAPI как `POST /bot/webhook`, который передает update в aiogram dispatcher.

Текст бота держать коротким. Основной интерфейс находится в Mini App, а не в переписке.

При начислении нового уровня backend может попробовать отправить пользователю сообщение через Bot API. Если отправка не удалась, действие пользователя не должно ломаться: XP все равно сохраняется, а ошибка уведомления только логируется.

## Local Development Steps

Все команды выполнять из `/home/pavel/pgu_project`. Не использовать git.

Создать `.env` на основе `.env.example`:

    APP_ENV=local
    DATABASE_URL=postgresql://healthquest:healthquest@localhost:5432/healthquest
    BOT_TOKEN=123456:replace_me
    WEBAPP_URL=https://replace-with-tunnel-url.example
    CORS_ORIGINS=http://localhost:5173
    DEV_TELEGRAM_USER_ID=100001
    DEV_TELEGRAM_FIRST_NAME=Dev
    BOT_MODE=polling

Поднять PostgreSQL:

    docker compose up -d postgres

Создать Python env и установить зависимости:

    cd /home/pavel/pgu_project/backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Применить миграции:

    cd /home/pavel/pgu_project/backend
    alembic upgrade head

Запустить backend:

    cd /home/pavel/pgu_project/backend
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Проверить health:

    curl http://localhost:8000/health

Ожидаемый ответ:

    {"status":"ok"}

Запустить frontend:

    cd /home/pavel/pgu_project/frontend
    npm install
    npm run dev -- --host 0.0.0.0

Открыть в браузере:

    http://localhost:5173

Для проверки именно внутри Telegram поднять HTTPS-туннель на frontend, записать URL в `.env` как `WEBAPP_URL`, перезапустить бота и открыть приложение через кнопку `/start`.

## Production Deployment Plan

На VPS использовать Docker Compose. Минимальная production-схема:

    postgres
      Хранит данные.

    backend
      FastAPI API, миграции запускаются перед стартом или отдельной командой.

    frontend
      Собирается в статические файлы.

    caddy
      Принимает HTTPS, отдает frontend и проксирует `/api/*` и `/bot/webhook` в backend.

    bot
      Нужен только если выбран long polling. Если выбран webhook, отдельный polling-сервис не нужен.

Для VPS рекомендуется webhook. Пример переменных:

    APP_ENV=production
    DATABASE_URL=postgresql://healthquest:<strong-password>@postgres:5432/healthquest
    BOT_TOKEN=<real-token>
    WEBAPP_URL=https://healthquest.example.com
    CORS_ORIGINS=https://healthquest.example.com
    BOT_MODE=webhook
    WEBHOOK_BASE_URL=https://healthquest.example.com
    WEBHOOK_SECRET=<random-long-secret>

Перед первым запуском на VPS:

    docker compose -f docker-compose.prod.yml up -d --build
    docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

После запуска:

    curl https://healthquest.example.com/health

Ожидаемый ответ:

    {"status":"ok"}

Затем написать боту `/start` и открыть Mini App. Если кнопка открывает белый экран, проверить URL frontend, CORS, доступность backend `/health` и наличие HTTPS-сертификата.

## Concrete Implementation Steps

Первый этап — создать backend skeleton. Добавить `backend/requirements.txt`, `backend/app/main.py`, `backend/app/config.py`, `backend/app/db.py`. После этого команда `uvicorn app.main:app --reload --port 8000` должна запускаться, а `GET /health` должен возвращать `{"status":"ok"}`.

Второй этап — добавить Alembic и модели. Создать `backend/alembic.ini`, `backend/alembic/env.py`, `backend/app/models.py` и миграцию `0001_initial_schema_and_seed.py`. После `alembic upgrade head` в PostgreSQL должны появиться таблицы, продукты и упражнения.

Третий этап — реализовать Telegram auth. Добавить `backend/app/auth.py`, dependency текущего пользователя и local dev fallback. Проверить вручную через Swagger UI или curl с `X-Dev-User: true`, что `/api/profile` создает dev-пользователя.

Четвертый этап — реализовать питание. Добавить роутеры `dictionaries.py` и `nutrition.py`, функции CRUD и расчет КБЖУ. Проверить: поиск `курица` возвращает куриную грудку, POST приема пищи на 150 г добавляет запись и увеличивает XP на 10.

Пятый этап — реализовать тренировки. Добавить `workouts.py`, создание тренировки, добавление подхода, выдачу предыдущего подхода и обновление личных рекордов. Проверить: подход `жим лежа 60 кг x 8` появляется в тренировке, рекорд в профиле становится 60 кг и 8 повторений, XP увеличивается на 5.

Шестой этап — реализовать бота. Добавить `/start` с кнопкой `web_app`. Локально запускать polling, на production предусмотреть webhook endpoint. Проверить: бот отправляет кнопку, Telegram открывает Mini App.

Седьмой этап — создать frontend. Сгенерировать Vite React app без TypeScript, подключить `api.js`, `telegram.js`, нижнюю навигацию и четыре экрана. Сначала сделать данные с API без полировки, затем довести дизайн.

Восьмой этап — отполировать UI. Настроить адаптивность под ширину 320-430px, проверить Telegram WebView, убрать любые переполнения текста, добавить loading/error/empty states, сделать кнопки и формы удобными для пальца.

Девятый этап — обновить `README.md`. Добавить краткие инструкции запуска локально, запуска через Telegram, production-переменные и решение по long polling/webhook.

## Validation and Acceptance

Автоматические тесты в этом проекте не писать. Приемка ручная.

Backend acceptance:

    cd /home/pavel/pgu_project/backend
    alembic upgrade head
    uvicorn app.main:app --reload --port 8000
    curl http://localhost:8000/health

Ожидается:

    {"status":"ok"}

Profile acceptance:

    curl -H "X-Dev-User: true" http://localhost:8000/api/profile

Ожидается JSON с `telegram_id`, `first_name`, `xp_total`, `level`, `xp_progress`.

Nutrition acceptance:

    Через frontend или Swagger UI найти продукт "Куриная грудка".
    Добавить прием пищи `lunch`, `product_id` куриной грудки, `grams` 150.
    Открыть экран "Сегодня".

Ожидается: в дневнике есть обед, калории и БЖУ рассчитаны примерно как 1.5 от значений на 100 г, XP вырос на 10.

Workout acceptance:

    Создать тренировку "Верх тела".
    Добавить подход: Жим лежа, 60 кг, 8 повторений.
    Открыть профиль.

Ожидается: XP вырос еще на 5, в личных рекордах появился жим лежа с 60 кг и 8 повторениями.

Telegram acceptance:

    Запустить frontend.
    Поднять HTTPS-туннель.
    Записать tunnel URL в WEBAPP_URL.
    Запустить бота в polling mode.
    Отправить /start в Telegram.
    Нажать кнопку открытия HealthQuest.

Ожидается: Mini App открывается внутри Telegram, профиль показывает Telegram-данные пользователя, действия сохраняются в PostgreSQL.

Production acceptance:

    docker compose -f docker-compose.prod.yml up -d --build
    docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
    curl https://healthquest.example.com/health

Ожидается: HTTPS работает, `/health` возвращает `{"status":"ok"}`, бот открывает production Mini App.

## Idempotence and Recovery

Все миграции Alembic должны быть повторяемыми на новом окружении: если удалить локальную БД и заново выполнить `alembic upgrade head`, схема и seed-данные должны восстановиться.

Если данные в локальной базе испорчены, можно остановить контейнер PostgreSQL, удалить только volume базы через Docker и заново применить миграции. Перед таким действием убедиться, что это локальная dev-база, а не production.

Удаление записей питания в MVP не откатывает XP, если не будет реализована отдельная логика компенсации. Это осознанное упрощение: XP является историей активности, а дневник питания — текущей записью дня.

Если Telegram Mini App не открывается локально, сначала проверить, что `WEBAPP_URL` начинается с `https://`, tunnel активен, frontend доступен по tunnel URL из обычного браузера, а бот был перезапущен после изменения `.env`.

Если production webhook не получает события, временно переключить `BOT_MODE=polling`, чтобы проверить токен и работу бота. После этого вернуться к webhook и проверить домен, HTTPS, endpoint `/bot/webhook` и `WEBHOOK_SECRET`.

## Artifacts and Notes

Ожидаемый минимальный ответ healthcheck:

    GET /health
    HTTP 200
    {"status":"ok"}

Пример успешной дневной сводки питания:

    {
      "date": "2026-04-25",
      "totals": {
        "calories": 248,
        "protein": 46.5,
        "fat": 5.4,
        "carbs": 0
      },
      "entries": [
        {
          "id": 1,
          "meal_type": "lunch",
          "product_name": "Куриная грудка",
          "grams": 150,
          "calories": 248
        }
      ]
    }

Пример профиля после добавления еды и подхода:

    {
      "telegram_id": 100001,
      "first_name": "Dev",
      "xp_total": 15,
      "level": 1,
      "xp_progress": 15,
      "xp_to_next": 100,
      "personal_records": [
        {
          "exercise_name": "Жим лежа",
          "max_weight_kg": 60,
          "max_reps": 8
        }
      ]
    }

## Interfaces and Dependencies

Backend public functions and modules that should exist by the end:

    backend/app/main.py
      app: FastAPI

    backend/app/db.py
      get_db()
      SessionLocal

    backend/app/auth.py
      validate_telegram_init_data(init_data: str, bot_token: str) -> dict
      get_current_user()

    backend/app/xp.py
      xp_for_meal_entry() -> int
      xp_for_workout_set() -> int
      calculate_level(xp_total: int) -> dict

    backend/app/crud.py
      upsert_user_from_telegram(db, telegram_user)
      search_foods(db, query)
      create_meal_entry(db, user, payload)
      get_today_nutrition(db, user)
      search_exercises(db, query, muscle_group)
      create_workout(db, user, payload)
      add_workout_set(db, user, workout_id, payload)
      get_previous_set(db, user, exercise_id)
      get_profile(db, user)

Frontend public helpers that should exist by the end:

    frontend/src/telegram.js
      getTelegram()
      getInitData()
      isTelegram()
      expandApp()
      hapticImpact()

    frontend/src/api.js
      apiFetch(path, options)

    frontend/src/App.jsx
      Главный компонент с загрузкой Telegram WebApp, нижней навигацией и экранами.

External services:

    Telegram Bot API
      Используется для команды /start, кнопки открытия Mini App и будущих уведомлений.

    Telegram Web App API
      Используется frontend-приложением для получения initData, темы, expand и haptic feedback.

    PostgreSQL
      Основное хранилище данных.

    Caddy или другой HTTPS reverse proxy на VPS
      Нужен для HTTPS, отдачи frontend и проксирования backend.

## Change Notes

2026-04-25 / Codex: Создан начальный самодостаточный план реализации MVP HealthQuest на основе ТЗ пользователя. Зафиксированы ограничения: без git, без тестов, без AI-фото, простая архитектура, FastAPI/PostgreSQL backend, React JavaScript frontend, seed-данные через Alembic, local long polling и production webhook для Telegram-бота.

2026-04-25 / Codex: Выполнена реализация MVP по плану. Добавлены backend, frontend, Alembic seed-миграция, Docker/Caddy production-схема и README. Обновлены команды с `python` на `python3`, потому что в текущем окружении команда `python` отсутствует.
