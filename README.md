# tg-bot — логистический Telegram-бот

Бот для поиска грузов, размещения заявок, рейтингов и откликов. Роли: заказчик, перевозчик, экспедитор.

## Требования

- Python 3.12+
- PostgreSQL
- Redis

## Переменные окружения

Скопируй `.env.example` в `.env` и заполни:

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather) |
| `BOT_USERNAME` | Username бота (опционально) |
| `DATABASE_URL` | PostgreSQL, формат: `postgresql+asyncpg://user:pass@host:port/db` |
| `REDIS_URL` | Redis, например `redis://localhost:6379` |
| `ADMIN_ID` | Telegram user_id администратора (алерты Watchdog) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Логин и пароль админ-панели |
| `SECRET_KEY` | Секрет для сессий админки (смени в продакшене) |
| `WEBAPP_URL` | Публичный URL для WebApp (если используешь) |
| `GROQ_API_KEY` | Ключ [Groq](https://console.groq.com) для умного поиска `/find` и AI (опционально) |
| `DEBUG` | `true` / `false` |

## Запуск

### Локально (uv)

```bash
uv sync
# PostgreSQL и Redis должны быть запущены
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker Compose

```bash
cp .env.example .env
# Отредактируй .env (BOT_TOKEN, ADMIN_ID и т.д.)
docker compose up -d
```

- Бот: порт 8001 (внутри контейнера 8000)
- Health: http://localhost:8001/health
- Админка: http://localhost:8001/admin

## Команды бота

- `/start` — меню / онбординг
- `/help` — справка
- `/find` — умный поиск грузов (нужен `GROQ_API_KEY` для парсинга запросов)
- `/me` — профиль
- `/remind 30m Текст` — напоминание
- `/reminders` — список напоминаний

## Структура

- `main.py` — FastAPI + lifespan, запуск бота и планировщика
- `src/bot/` — хендлеры, клавиатуры, FSM
- `src/core/` — БД, Redis, AI, сервисы (watchdog, рейтинг, заявки)
- `src/admin/` — веб-админка
- `src/webapp/` — WebApp
- `migrations/` — SQL-миграции схемы
