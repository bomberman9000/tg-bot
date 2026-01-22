import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import get_settings
from src.core.logger import logger
from src.core.redis import get_redis, close_redis

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.bot.bot import bot, dp
    from src.bot.handlers.start import router as start_router
    from src.bot.handlers.feedback import router as feedback_router
    
    logger.info("Starting bot...")
    
    redis = await get_redis()
    await redis.ping()
    logger.info("Redis connected")
    
    dp.include_router(start_router)
    dp.include_router(feedback_router)
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
    redis_ok = await redis.ping()
    return {"status": "ok", "redis": redis_ok}

@app.get("/")
async def root():
    return {"message": "Bot API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
