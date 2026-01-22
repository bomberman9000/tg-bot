from aiogram import Router
from aiogram.types import ErrorEvent
from src.core.logger import logger
from src.core.config import get_settings
from src.bot.bot import bot

router = Router()

@router.error()
async def error_handler(event: ErrorEvent):
    logger.error(f"Error: {event.exception}", exc_info=True)
    
    settings = get_settings()
    if settings.admin_id:
        try:
            await bot.send_message(
                settings.admin_id,
                f"❌ <b>Ошибка бота:</b>\n\n<code>{event.exception}</code>"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
