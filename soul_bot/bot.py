import asyncio
import logging
import time

from bot.loader import bot
from bot.middlewares.events import EventsMiddleware
from bot.workers import schedule_
from logging_config import configure_logging
from bot.handlers.error import register_error_handlers

logger = logging.getLogger(__name__)


async def wait_for_db(max_retries: int = 30, delay: int = 1):
    """Wait for database to be ready with retry logic"""
    from database.database import db
    from sqlalchemy.exc import OperationalError
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔄 Attempting to connect to database (attempt {attempt}/{max_retries})...")
            await db.ensure_ready()
            logger.info("✅ Database connection successful!")
            return True
        except (ConnectionRefusedError, OSError, OperationalError) as e:
            if attempt < max_retries:
                logger.warning(f"⏳ Database not ready yet: {type(e).__name__}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"❌ Failed to connect to database after {max_retries} attempts")
                raise
        except Exception as e:
            logger.error(f"❌ Unexpected database error: {e}")
            raise
    
    return False


async def main():
    await bot.delete_webhook(drop_pending_updates=False)
    from bot.handlers import dp

    dp.message.middleware(EventsMiddleware())
    dp.callback_query.middleware(EventsMiddleware())
    register_error_handlers(dp)

    # Wait for database to be ready
    await wait_for_db()
    
    # Create tables using SQLAlchemy models
    from database.database import create_tables, db
    await create_tables()
    logger.info("✅ Database tables created/verified")
    
    # Run pending SQL migrations
    from database.migration_runner import run_migrations
    await run_migrations(db.engine)
    logger.info("✅ Migrations applied")
    
    # Start database health monitor
    from database.resilience import DatabaseHealthMonitor
    health_monitor = DatabaseHealthMonitor(db, check_interval=60)
    asyncio.create_task(health_monitor.monitor())
    logger.info("✅ Database health monitor started")
    
    asyncio.create_task(schedule_())
    #await logger.start()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
