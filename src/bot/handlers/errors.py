from aiogram import Router
from aiogram.types import ErrorEvent
from src.core.logger import logger
from src.core.config import get_settings
from src.bot.bot import bot

router = Router()

@router.error()
async def error_handler(event: ErrorEvent):
    logger.error(f"Error: {event.exception}")
    settings = get_settings()
    if settings.admin_id:
        try:
            error_text = str(event.exception)[:500]
            await bot.send_message(
                settings.admin_id,
                f"❌ Ошибка бота:\n\n<code>{error_text}</code>"
            )
        except:
            pass
