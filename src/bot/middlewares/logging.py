from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from src.core.logger import logger
from src.core.redis import get_redis

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        redis = await get_redis()
        
        if isinstance(event, Message) and event.text:
            logger.info(f"[{user.id}] {user.full_name}: {event.text}")
            await redis.hincrby("stats:users", str(user.id), 1)
            await redis.incr("stats:messages")
        elif isinstance(event, CallbackQuery):
            logger.info(f"[{user.id}] {user.full_name} callback: {event.data}")
            await redis.incr("stats:callbacks")
        
        return await handler(event, data)
