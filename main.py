import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import settings
from src.core.logger import logger
from src.core.redis import get_redis, close_redis
from src.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.bot.bot import bot, dp
    from src.bot.handlers.start import router as start_router
    from src.bot.handlers.feedback import router as feedback_router
    from src.bot.handlers.admin import router as admin_router
    from src.bot.handlers.errors import router as errors_router
    from src.bot.middlewares.logging import LoggingMiddleware
    
    logger.info("Starting bot...")
    
    await init_db()
    logger.info("Database initialized")
    
    redis = await get_redis()
    await redis.ping()
    logger.info("Redis connected")
    
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(feedback_router)
    dp.include_router(errors_router)
    
    polling_task = asyncio.create_task(dp.start_polling(bot))
    logger.info("Bot polling started")
    yield
    logger.info("Shutting down...")
    polling_task.cancel()
    await bot.session.close()
    await close_redis()

app = FastAPI(title="TG Bot API", lifespan=lifespan)

@app.get("/api/health")
async def health():
    redis = await get_redis()
    return {"status": "ok", "redis": await redis.ping()}

@app.get("/")
async def root():
    return {"message": "Bot API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
