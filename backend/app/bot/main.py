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
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
