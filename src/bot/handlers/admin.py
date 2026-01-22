from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func
from src.core.config import get_settings
from src.core.redis import get_redis
from src.core.database import async_session
from src.core.models import User, Feedback
from src.bot.bot import bot

router = Router()

def admin_filter(message: Message) -> bool:
    settings = get_settings()
    return message.from_user.id == settings.admin_id

@router.message(Command("stats"), admin_filter)
async def admin_stats(message: Message):
    redis = await get_redis()
    async with async_session() as session:
        users_count = await session.scalar(select(func.count()).select_from(User))
        feedback_count = await session.scalar(select(func.count()).select_from(Feedback))
    messages = await redis.get("stats:messages") or 0
    callbacks = await redis.get("stats:callbacks") or 0
    text = f"📊 Статистика:\n👥 {users_count}\n💬 {messages}\n🔘 {callbacks}\n📝 {feedback_count}"
    await message.answer(text)

@router.message(Command("users"), admin_filter)
async def admin_users(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).limit(20))
        users = result.scalars().all()
    if not users:
        await message.answer("👥 Пользователей нет")
        return
    text = "👥 Пользователи:\n\n"
    for u in users:
        ban = "🚫" if u.is_banned else ""
        text += f"• {u.id} - {u.full_name} {ban}\n"
    await message.answer(text)

@router.message(Command("ban"), admin_filter)
async def admin_ban(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /ban USER_ID")
        return
    user_id = int(args[1])
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_banned = True
            await session.commit()
            await message.answer(f"🚫 {user.full_name} забанен")
        else:
            await message.answer("❌ Пользователь не найден")

@router.message(Command("unban"), admin_filter)
async def admin_unban(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /unban USER_ID")
        return
    user_id = int(args[1])
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_banned = False
            await session.commit()
            await message.answer(f"✅ {user.full_name} разбанен")
        else:
            await message.answer("❌ Пользователь не найден")

@router.message(Command("broadcast"), admin_filter)
async def admin_broadcast(message: Message):
    if not message.reply_to_message:
        await message.answer("↩️ Ответь на сообщение для рассылки")
        return
    async with async_session() as session:
        result = await session.execute(select(User).where(User.is_banned == False))
        users = result.scalars().all()
    sent, failed = 0, 0
    for user in users:
        try:
            await message.reply_to_message.copy_to(user.id)
            sent += 1
        except:
            failed += 1
    await message.answer(f"✅ Отправлено: {sent}\n❌ Ошибок: {failed}")

@router.message(Command("feedback_list"), admin_filter)
async def admin_feedback(message: Message):
    async with async_session() as session:
        result = await session.execute(select(Feedback).order_by(Feedback.id.desc()).limit(10))
        feedbacks = result.scalars().all()
    if not feedbacks:
        await message.answer("📭 Фидбек пуст")
        return
    text = "📝 Последний фидбек:\n\n"
    for fb in feedbacks:
        text += f"• [{fb.user_id}] {fb.message[:50]}\n"
    await message.answer(text)
