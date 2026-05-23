import asyncio

from aiogram import Bot

from app.bot.handlers import create_dispatcher
from app.config import get_settings


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required to run the Telegram bot")

    bot = Bot(token=settings.bot_token)
    dispatcher = create_dispatcher()

    if settings.bot_mode == "webhook":
        base_url = settings.webhook_base_url or settings.webapp_url
        if not base_url:
            raise RuntimeError("WEBHOOK_BASE_URL or WEBAPP_URL is required for webhook mode")

        await bot.set_webhook(
            url=f"{base_url.rstrip('/')}/bot/webhook",
            secret_token=settings.webhook_secret or None,
            drop_pending_updates=True,
        )
        print("Webhook registered. Run FastAPI app to receive updates.")
        await asyncio.Event().wait()
        return

    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
