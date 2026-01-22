from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Привет, {message.from_user.full_name}!")

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Доступные команды:\n/start - Начать\n/help - Помощь")
