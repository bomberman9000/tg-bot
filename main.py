import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import settings
from src.core.logger import logger
from src.core.redis import get_redis, close_redis
from src.core.database import init_db
from src.core.scheduler import setup_scheduler, scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.bot.bot import bot, dp
    from src.bot.handlers.start import router as start_router
    from src.bot.handlers.feedback import router as feedback_router
    from src.bot.handlers.admin import router as admin_router
    from src.bot.handlers.errors import router as errors_router
    from src.bot.handlers.reminder import router as reminder_router
    from src.bot.handlers.cargo import router as cargo_router
    from src.bot.handlers.search import router as search_router
    from src.bot.handlers.rating import router as rating_router
    from src.bot.handlers.profile import router as profile_router
    from src.bot.handlers.analytics import router as analytics_router
    from src.bot.handlers.chat import router as chat_router
    from src.bot.handlers.antifraud import router as antifraud_router
    from src.bot.middlewares.logging import LoggingMiddleware
    
    logger.info("Starting bot...")
    
    await init_db()
    logger.info("Database initialized")
    
    redis = await get_redis()
    await redis.ping()
    logger.info("Redis connected")
    
    setup_scheduler()
    
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.include_router(admin_router)
    dp.include_router(cargo_router)
    dp.include_router(search_router)
    dp.include_router(rating_router)
    dp.include_router(profile_router)
    dp.include_router(analytics_router)
    dp.include_router(chat_router)
    dp.include_router(antifraud_router)
    dp.include_router(start_router)
    dp.include_router(feedback_router)
    dp.include_router(errors_router)
    dp.include_router(reminder_router)
    
    polling_task = asyncio.create_task(dp.start_polling(bot))
    logger.info("Bot polling started")
    yield
    logger.info("Shutting down...")
    scheduler.shutdown()
    polling_task.cancel()
    await bot.session.close()
    await close_redis()

app = FastAPI(title="Logistics Bot API", lifespan=lifespan)

@app.get("/api/health")
async def health():
    redis = await get_redis()
    return {"status": "ok", "redis": await redis.ping()}

@app.get("/api/stats")
async def api_stats():
    from src.core.database import async_session
    from src.core.models import User, Cargo, RouteSubscription, Report
    from sqlalchemy import select, func
    
    async with async_session() as session:
        users = await session.scalar(select(func.count()).select_from(User))
        cargos = await session.scalar(select(func.count()).select_from(Cargo))
        reports = await session.scalar(select(func.count()).select_from(Report))
    
    return {"users": users, "cargos": cargos, "reports": reports}

@app.get("/api/cargos")
async def api_cargos(from_city: str = None, to_city: str = None):
    from src.core.database import async_session
    from src.core.models import Cargo, CargoStatus
    from sqlalchemy import select
    
    async with async_session() as session:
        query = select(Cargo).where(Cargo.status == CargoStatus.NEW)
        if from_city:
            query = query.where(Cargo.from_city.ilike(f"%{from_city}%"))
        if to_city:
            query = query.where(Cargo.to_city.ilike(f"%{to_city}%"))
        result = await session.execute(query.limit(50))
        cargos = result.scalars().all()
    
    return [{"id": c.id, "from": c.from_city, "to": c.to_city, "weight": c.weight, "price": c.price} for c in cargos]

@app.get("/")
async def root():
    return {"message": "Logistics Bot API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
