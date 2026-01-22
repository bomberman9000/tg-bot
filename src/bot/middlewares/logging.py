from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from src.core.logger import logger
from src.core.redis import get_redis
from src.core.database import async_session
from src.core.models import User

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: Message | CallbackQuery, data: Dict) -> Any:
        user = event.from_user
        redis = await get_redis()
        
        # Сохраняем юзера в БД
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user.id))
            db_user = result.scalar_one_or_none()
            if not db_user:
                db_user = User(id=user.id, username=user.username, full_name=user.full_name)
                session.add(db_user)
                await session.commit()
                logger.info(f"New user: {user.id} {user.full_name}")
        
        if isinstance(event, Message) and event.text:
            logger.info(f"[{user.id}] {user.full_name}: {event.text}")
            await redis.hincrby("stats:users", str(user.id), 1)
            await redis.incr("stats:messages")
        elif isinstance(event, CallbackQuery):
            logger.info(f"[{user.id}] callback: {event.data}")
            await redis.incr("stats:callbacks")
        
        return await handler(event, data)
