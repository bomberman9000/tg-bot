from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from sqlalchemy import select
from src.core.logger import logger

scheduler = AsyncIOScheduler()

async def daily_stats_job():
    from src.bot.bot import bot
    from src.core.config import settings
    from src.core.redis import get_redis
    from src.core.database import async_session
    from src.core.models import User
    from sqlalchemy import func
    
    if not settings.admin_id:
        return
    
    redis = await get_redis()
    async with async_session() as session:
        users_count = await session.scalar(select(func.count()).select_from(User))
    
    messages = await redis.get("stats:messages") or 0
    
    await bot.send_message(
        settings.admin_id,
        f"📊 Ежедневный отчёт:\n\n👥 Пользователей: {users_count}\n💬 Сообщений: {messages}"
    )
    logger.info("Daily stats sent")

async def check_reminders_job():
    from src.bot.bot import bot
    from src.core.database import async_session
    from src.core.models import Reminder
    
    async with async_session() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.is_sent == False)
            .where(Reminder.remind_at <= datetime.utcnow())
        )
        reminders = result.scalars().all()
        
        for r in reminders:
            try:
                await bot.send_message(r.user_id, f"⏰ Напоминание:\n\n{r.text}")
                r.is_sent = True
                logger.info(f"Reminder sent to {r.user_id}")
            except Exception as e:
                logger.error(f"Failed to send reminder: {e}")
        
        await session.commit()

def setup_scheduler():
    scheduler.add_job(daily_stats_job, CronTrigger(hour=9, minute=0), id="daily_stats")
    scheduler.add_job(check_reminders_job, IntervalTrigger(seconds=30), id="check_reminders")
    scheduler.start()
    logger.info("Scheduler started")
