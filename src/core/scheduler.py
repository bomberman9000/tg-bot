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

async def archive_old_cargos_job():
    from src.core.database import async_session
    from src.core.models import Cargo, CargoStatus

    cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    async with async_session() as session:
        result = await session.execute(
            select(Cargo)
            .where(Cargo.status == CargoStatus.NEW)
            .where(Cargo.load_date < cutoff)
        )
        cargos = result.scalars().all()

        for cargo in cargos:
            cargo.status = CargoStatus.ARCHIVED

        if cargos:
            await session.commit()
            logger.info("Archived cargos: %s", len(cargos))


async def push_notifications_job():
    """Find cargos created in the last 5 min that haven't been notified yet."""
    from datetime import timedelta
    from src.core.database import async_session
    from src.core.models import Cargo, CargoStatus
    from src.core.services.notifications import notify_subscribers

    cutoff = datetime.utcnow() - timedelta(minutes=6)
    async with async_session() as session:
        result = await session.execute(
            select(Cargo)
            .where(Cargo.status == CargoStatus.NEW)
            .where(Cargo.notified_at.is_(None))
            .where(Cargo.created_at >= cutoff)
        )
        cargos = result.scalars().all()

        for cargo in cargos:
            try:
                await notify_subscribers(cargo)
                cargo.notified_at = datetime.utcnow()
            except Exception as e:
                logger.error("Push notification error for cargo #%s: %s", cargo.id, e)

        if cargos:
            await session.commit()
            logger.info("Push-notified %d new cargos", len(cargos))


def setup_scheduler():
    scheduler.add_job(daily_stats_job, CronTrigger(hour=9, minute=0), id="daily_stats")
    scheduler.add_job(check_reminders_job, IntervalTrigger(seconds=30), id="check_reminders")
    scheduler.add_job(archive_old_cargos_job, CronTrigger(hour=0, minute=10), id="archive_cargos")
    scheduler.add_job(push_notifications_job, IntervalTrigger(minutes=5), id="push_notifications")
    scheduler.start()
    logger.info("Scheduler started")
