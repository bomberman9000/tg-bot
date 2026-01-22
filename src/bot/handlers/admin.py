from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from src.core.config import get_settings
from src.core.redis import get_redis
from src.bot.bot import bot

router = Router()

def admin_filter(message: Message) -> bool:
    settings = get_settings()
    return message.from_user.id == settings.admin_id

@router.message(Command("stats"), admin_filter)
async def admin_stats(message: Message):
    redis = await get_redis()
    messages = await redis.get("stats:messages") or 0
    callbacks = await redis.get("stats:callbacks") or 0
    users_count = await redis.hlen("stats:users")
    feedback_count = await redis.llen("feedback")
    text = f"📊 Статистика:\n👥 {users_count}\n💬 {messages}\n🔘 {callbacks}\n📝 {feedback_count}"
    await message.answer(text)

@router.message(Command("feedback_list"), admin_filter)
async def admin_feedback(message: Message):
    redis = await get_redis()
    feedbacks = await redis.lrange("feedback", 0, 9)
    if not feedbacks:
        await message.answer("📭 Фидбек пуст")
        return
    text = "📝 Последний фидбек:\n\n"
    for i, fb in enumerate(feedbacks, 1):
        text += f"{i}. {fb}\n"
    await message.answer(text)

@router.message(Command("broadcast"), admin_filter)
async def admin_broadcast(message: Message):
    if not message.reply_to_message:
        await message.answer("↩️ Ответь на сообщение для рассылки")
        return
    redis = await get_redis()
    user_ids = await redis.hkeys("stats:users")
    sent = 0
    failed = 0
    for user_id in user_ids:
        try:
            await message.reply_to_message.copy_to(int(user_id))
            sent += 1
        except:
            failed += 1
    await message.answer(f"✅ Отправлено: {sent}\n❌ Ошибок: {failed}")

@router.message(Command("users"), admin_filter)
async def admin_users(message: Message):
    redis = await get_redis()
    users = await redis.hgetall("stats:users")
    if not users:
        await message.answer("👥 Пользователей нет")
        return
    text = "👥 Пользователи:\n\n"
    for uid, count in list(users.items())[:20]:
        text += f"• {uid}: {count} сообщ.\n"
    await message.answer(text)
