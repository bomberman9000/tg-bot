from aiogram import Router
from aiogram.types import ErrorEvent
from src.core.config import settings
from src.core.logger import logger
from src.bot.bot import bot

router = Router()

@router.error()
async def error_handler(event: ErrorEvent):
    logger.error(f"Error: {event.exception}", exc_info=event.exception)
    
    if settings.admin_id:
        try:
            await bot.send_message(
                settings.admin_id,
                f"🚨 <b>Ошибка:</b>\n\n<code>{str(event.exception)[:500]}</code>"
            )
        except:
            pass
