from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from src.bot.keyboards import main_menu
from src.bot.handlers.cargo import send_cargo_details
from src.core.database import async_session
from src.core.models import User, Reminder

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) == 2 and parts[1].startswith("cargo_"):
            try:
                cargo_id = int(parts[1].split("_")[1])
            except:
                cargo_id = None
            if cargo_id:
                await send_cargo_details(message, cargo_id)
                return
    await message.answer(
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n\n"
        f"Выбери действие в меню ниже.",
        reply_markup=main_menu()
    )

@router.callback_query(F.data == "menu")
async def show_menu(cb: CallbackQuery):
    try:
        await cb.message.edit_text("🏠 <b>Главное меню</b>", reply_markup=main_menu())
    except TelegramBadRequest:
        await cb.message.answer("🏠 <b>Главное меню</b>", reply_markup=main_menu())
    await cb.answer()

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📚 <b>Как пользоваться:</b>\n\n"
        "Основные действия — через кнопки меню:\n"
        "🚛 Найти груз\n"
        "📦 Разместить груз\n"
        "🧾 Мои грузы\n"
        "🤝 Мои отклики\n"
        "⭐ Рейтинг / Профиль\n"
        "🆘 Поддержка\n\n"
        "<b>Команды:</b>\n"
        "/start — меню\n"
        "/help — помощь\n"
        "/me — мой профиль\n"
        "/remind 30m Текст — напоминание\n"
        "/reminders — мои напоминания"
    )

@router.message(Command("me"))
async def cmd_me(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        reminders = await session.execute(
            select(Reminder)
            .where(Reminder.user_id == message.from_user.id)
            .where(Reminder.is_sent == False)
        )
        rem_count = len(reminders.scalars().all())
    
    if user:
        status = "🚫 Забанен" if user.is_banned else "✅ Активен"
        await message.answer(
            f"👤 <b>Твой профиль:</b>\n\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📝 Имя: {user.full_name}\n"
            f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n"
            f"⏰ Напоминаний: {rem_count}\n"
            f"Статус: {status}"
        )
