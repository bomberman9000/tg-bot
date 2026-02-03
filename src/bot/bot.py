from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InaccessibleMessage
from aiogram.exceptions import TelegramBadRequest
from src.core.config import settings

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

async def _inaccessible_edit_text(self, text: str, **kwargs):
    chat = getattr(self, "chat", None)
    if not chat:
        return None
    try:
        return await bot.send_message(
            chat.id,
            text,
            reply_markup=kwargs.get("reply_markup"),
            disable_web_page_preview=kwargs.get("disable_web_page_preview", True),
        )
    except TelegramBadRequest:
        return None

async def _inaccessible_answer(self, text: str, **kwargs):
    chat = getattr(self, "chat", None)
    if not chat:
        return None
    try:
        return await bot.send_message(chat.id, text, **kwargs)
    except TelegramBadRequest:
        return None

InaccessibleMessage.edit_text = _inaccessible_edit_text
InaccessibleMessage.answer = _inaccessible_answer
