from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from src.core.config import settings

bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
