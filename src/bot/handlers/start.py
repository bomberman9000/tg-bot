from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy import select
from src.bot.keyboards import main_menu
from src.core.database import async_session
from src.core.models import User, Reminder

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"👋 Привет, <b>{message.from_user.full_name}</b>!", reply_markup=main_menu())

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📚 <b>Команды:</b>\n\n"
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
