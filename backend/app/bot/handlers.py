from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.config import get_settings

router = Router()


def mini_app_keyboard() -> InlineKeyboardMarkup:
    settings = get_settings()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть HealthQuest",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ]
    )


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(
        "HealthQuest готов. Открой приложение и отметь питание или тренировку.",
        reply_markup=mini_app_keyboard(),
    )


@router.message(Command("help"))
async def help_message(message: Message) -> None:
    await message.answer("Нажми кнопку в /start, чтобы открыть HealthQuest.", reply_markup=mini_app_keyboard())


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher
