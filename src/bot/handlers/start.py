from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from src.bot.keyboards import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n\n"
        "Выбери действие:",
        reply_markup=main_menu()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📚 <b>Команды:</b>\n\n"
        "/start - Главное меню\n"
        "/help - Помощь"
    )
