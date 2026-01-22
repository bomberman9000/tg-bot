from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from src.core.config import get_settings
from src.core.redis import get_redis

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
