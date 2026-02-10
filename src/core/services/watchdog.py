"""
Watchdog агент: мониторинг здоровья бота, автоперезапуск, уведомления
"""

import asyncio
from datetime import datetime

import httpx

from src.core.config import settings
from src.core.logger import logger


class BotWatchdog:
    def __init__(self):
        self.last_activity = datetime.utcnow()
        self.error_count = 0
        self.restart_count = 0
        self.is_healthy = True
        self.checks: list[dict] = []

    def heartbeat(self):
        """Обновить время последней активности"""
        self.last_activity = datetime.utcnow()
        self.error_count = 0
        self.is_healthy = True

    def record_error(self, error: str):
        """Записать ошибку"""
        self.error_count += 1
        self.checks.append({
            "time": datetime.utcnow().isoformat(),
            "type": "error",
            "message": error[:200],
        })
        self.checks = self.checks[-50:]

        if self.error_count >= 5:
            self.is_healthy = False

    async def check_health(self) -> dict:
        """Проверка здоровья системы"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "bot_healthy": self.is_healthy,
            "last_activity": self.last_activity.isoformat(),
            "error_count": self.error_count,
            "restart_count": self.restart_count,
            "checks": {},
        }

        # Redis
        try:
            from src.core.redis import get_redis
            redis = await get_redis()
            await redis.ping()
            results["checks"]["redis"] = "✅ OK"
        except Exception as e:
            results["checks"]["redis"] = f"❌ Error: {e}"

        # PostgreSQL
        try:
            from src.core.database import async_session
            from sqlalchemy import text
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
            results["checks"]["postgres"] = "✅ OK"
        except Exception as e:
            results["checks"]["postgres"] = f"❌ Error: {e}"

        # Telegram API
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://api.telegram.org/bot{settings.bot_token}/getMe"
                )
                if resp.status_code == 200:
                    results["checks"]["telegram"] = "✅ OK"
                else:
                    results["checks"]["telegram"] = (
                        f"⚠️ Status {resp.status_code}"
                    )
        except Exception as e:
            results["checks"]["telegram"] = f"❌ Error: {e}"

        # Memory
        try:
            import os
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            results["checks"]["memory"] = f"✅ {memory_mb:.1f} MB"
            if memory_mb > 500:
                results["checks"]["memory"] = (
                    f"⚠️ High: {memory_mb:.1f} MB"
                )
        except Exception:
            results["checks"]["memory"] = "⚠️ psutil not available"

        # Idle
        idle_seconds = (
            datetime.utcnow() - self.last_activity
        ).total_seconds()
        if idle_seconds > 300:
            results["checks"]["activity"] = f"⚠️ Idle {idle_seconds:.0f}s"
        else:
            results["checks"]["activity"] = (
                f"✅ Active ({idle_seconds:.0f}s ago)"
            )

        return results

    def format_status(self, health: dict) -> str:
        """Форматирует статус для отправки"""
        status = (
            "🟢 Здоров" if health["bot_healthy"] else "🔴 Проблемы"
        )

        text = "🤖 <b>Статус бота</b>\n\n"
        text += f"📊 Состояние: {status}\n"
        text += f"⏱ Проверка: {health['timestamp'][:19]}\n"
        text += f"🔄 Перезапусков: {health['restart_count']}\n"
        text += f"❌ Ошибок: {health['error_count']}\n\n"
        text += "<b>Компоненты:</b>\n"
        for name, status_val in health["checks"].items():
            text += f"• {name}: {status_val}\n"
        return text


watchdog = BotWatchdog()


async def notify_admin(message: str):
    """Отправить уведомление админу"""
    if settings.admin_id is None:
        return
    try:
        from src.bot.bot import bot
        await bot.send_message(
            settings.admin_id,
            f"🚨 <b>Watchdog Alert</b>\n\n{message}",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Failed to notify admin: %s", e)


async def watchdog_loop():
    """Фоновый цикл мониторинга"""
    while True:
        try:
            await asyncio.sleep(60)

            health = await watchdog.check_health()

            if not health["bot_healthy"]:
                await notify_admin(
                    "Обнаружены проблемы!\n\n"
                    f"Ошибок: {health['error_count']}\n"
                    f"Последняя активность: {health['last_activity']}"
                )

            for name, status in health["checks"].items():
                if "❌" in str(status):
                    await notify_admin(
                        f"Компонент {name} недоступен:\n{status}"
                    )

        except Exception as e:
            logger.error("Watchdog loop error: %s", e)
            await asyncio.sleep(30)
