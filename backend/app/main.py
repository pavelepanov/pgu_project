from aiogram import Bot
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from .bot.handlers import create_dispatcher
from .config import get_settings
from .routers import dictionaries, nutrition, profile, stats, tracking, workouts

settings = get_settings()

app = FastAPI(title="HealthQuest API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(dictionaries.router)
app.include_router(nutrition.router)
app.include_router(workouts.router)
app.include_router(stats.router)
app.include_router(tracking.router)

bot = Bot(token=settings.bot_token) if settings.bot_token else None
dispatcher = create_dispatcher()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.on_event("startup")
async def configure_telegram_webhook() -> None:
    if bot is None or settings.bot_mode != "webhook":
        return

    base_url = settings.webhook_base_url or settings.webapp_url
    if not base_url:
        return

    await bot.set_webhook(
        url=f"{base_url.rstrip('/')}/bot/webhook",
        secret_token=settings.webhook_secret or None,
        drop_pending_updates=True,
    )


@app.on_event("shutdown")
async def close_telegram_bot() -> None:
    if bot is not None:
        await bot.session.close()


@app.post("/bot/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> dict:
    if settings.webhook_secret and x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook secret")
    if bot is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="BOT_TOKEN is not configured")

    payload = await request.json()
    update = Update.model_validate(payload, context={"bot": bot})
    await dispatcher.feed_update(bot, update)
    return {"ok": True}
