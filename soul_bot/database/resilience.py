"""
Database connection resilience utilities.
Automatically retries failed operations due to connection issues.
"""
import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar, Any

from sqlalchemy.exc import OperationalError, DBAPIError
from asyncpg.exceptions import (
    ConnectionDoesNotExistError,
    ConnectionRejectionError,
    InterfaceError,
    PostgresConnectionError,
)

from bot.services.error_notifier import schedule_exception_report

logger = logging.getLogger(__name__)

T = TypeVar('T')


# Connection errors that should trigger a retry
RETRIABLE_ERRORS = (
    OperationalError,
    DBAPIError,
    ConnectionDoesNotExistError,
    ConnectionRejectionError,
    InterfaceError,
    PostgresConnectionError,
    ConnectionError,
    OSError,  # Can happen with network issues
)


def is_retriable_error(error: Exception) -> bool:
    """Check if an error is retriable (connection issue vs. data issue)."""
    if isinstance(error, RETRIABLE_ERRORS):
        return True
    
    # Check error messages for connection-related issues
    error_msg = str(error).lower()
    connection_keywords = [
        'connection', 'timeout', 'network', 'closed', 'terminated',
        'refused', 'reset', 'broken pipe', 'server closed',
        'cannot connect', 'connection pool', 'pool timeout'
    ]
    
    return any(keyword in error_msg for keyword in connection_keywords)


def is_missing_table_error(error: Exception) -> bool:
    """Check if error is due to missing table (PostgreSQL crash recovery scenario)."""
    error_msg = str(error).lower()
    return (
        'does not exist' in error_msg or
        'undefined table' in error_msg or
        'relation' in error_msg and 'does not exist' in error_msg
    )


def with_db_retry(
    max_retries: int = 3,
    base_delay: float = 0.5,
    backoff_multiplier: float = 2.0,
    log_failures: bool = True,
    auto_recreate_tables: bool = True
):
    """
    Decorator that retries database operations on connection failures.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        backoff_multiplier: Multiplier for exponential backoff
        log_failures: Whether to log retry attempts
        auto_recreate_tables: Auto-recreate tables if they're missing (crash recovery)
    
    Usage:
        @with_db_retry(max_retries=3)
        async def get_user(user_id: int):
            async with db() as session:
                return await session.execute(...)
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay
            table_recreated = False
            
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # CRITICAL: Check if table is missing (PostgreSQL crash/restart scenario)
                    if auto_recreate_tables and is_missing_table_error(e) and not table_recreated:
                        logger.error(
                            f"🚨 CRITICAL: Table missing in {func.__name__}! "
                            f"PostgreSQL may have crashed/restarted. Attempting recovery..."
                        )
                        try:
                            # Attempt to recreate all tables
                            from database.database import create_tables
                            await create_tables()
                            logger.info("✅ Tables recreated successfully, retrying operation...")
                            table_recreated = True
                            # Retry immediately after table recreation
                            await asyncio.sleep(0.5)
                            continue
                        except Exception as recreate_error:
                            logger.error(f"❌ Failed to recreate tables: {recreate_error}")
                            schedule_exception_report(
                                "database.recreate_tables",
                                recreate_error,
                                extras={"function": func.__name__},
                            )
                            raise
                    
                    # Check if error is retriable (connection issues)
                    if not is_retriable_error(e):
                        # Not a connection issue - fail immediately
                        logger.error(f"❌ Non-retriable error in {func.__name__}: {e}")
                        schedule_exception_report(
                            "database.non_retriable",
                            e,
                            extras={"function": func.__name__},
                        )
                        raise
                    
                    # Last attempt - don't retry anymore
                    if attempt == max_retries:
                        if log_failures:
                            logger.error(
                                f"❌ {func.__name__} failed after {max_retries} retries: {e}"
                            )
                        schedule_exception_report(
                            "database.retry_exhausted",
                            e,
                            extras={"function": func.__name__, "retries": max_retries},
                        )
                        raise
                    
                    # Log retry attempt
                    if log_failures:
                        logger.warning(
                            f"⚠️  {func.__name__} failed (attempt {attempt}/{max_retries}), "
                            f"retrying in {delay:.1f}s: {type(e).__name__}: {e}"
                        )
                    
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(delay)
                    delay *= backoff_multiplier
            
            # Should never reach here, but just in case
            if last_exception:
                schedule_exception_report(
                    "database.retry_unknown",
                    last_exception,
                    extras={"function": func.__name__},
                )
            raise last_exception
        
        return wrapper
    return decorator


class DatabaseHealthMonitor:
    """
    Monitors database health and attempts recovery.
    Can be run as a background task.
    """
    
    def __init__(self, db_manager, check_interval: int = 60):
        """
        Args:
            db_manager: DatabaseManager instance
            check_interval: Seconds between health checks
        """
        self.db_manager = db_manager
        self.check_interval = check_interval
        self.is_healthy = True
        self.consecutive_failures = 0
        
    async def check_health(self) -> bool:
        """Perform a simple health check query and verify critical tables exist."""
        try:
            from sqlalchemy import text
            async with self.db_manager.engine.connect() as conn:
                # Basic connection check
                await conn.execute(text("SELECT 1"))
                
                # Verify critical table exists (aiogram_states is essential for bot)
                result = await conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = 'aiogram_states')"
                ))
                table_exists = result.scalar()
                
                if not table_exists:
                    logger.error("🚨 CRITICAL: aiogram_states table is missing!")
                    return False
                
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    async def recover(self) -> bool:
        """Attempt to recover database connection and recreate tables if missing."""
        logger.warning("🔄 Attempting database recovery...")
        try:
            # Ensure connection is ready
            await self.db_manager.ensure_ready()
            
            # Recreate tables if they're missing
            from database.database import create_tables
            await create_tables()
            
            logger.info("✅ Database recovered successfully (connection + tables)")
            return True
        except Exception as e:
            logger.error(f"❌ Database recovery failed: {e}")
            schedule_exception_report(
                "database.recover_failed",
                e,
                extras={"check_interval": self.check_interval},
            )
            return False
    
    async def monitor(self) -> None:
        """
        Run continuous health monitoring.
        Call this as a background task: asyncio.create_task(monitor.monitor())
        """
        logger.info(f"🔍 Database health monitor started (interval: {self.check_interval}s)")
        
        while True:
            try:
                healthy = await self.check_health()
                
                if healthy:
                    if not self.is_healthy:
                        logger.info("✅ Database is back online")
                    self.is_healthy = True
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1
                    self.is_healthy = False
                    
                    logger.warning(
                        f"⚠️  Database unhealthy (consecutive failures: {self.consecutive_failures})"
                    )
                    
                    # Attempt recovery after 2 consecutive failures
                    if self.consecutive_failures >= 2:
                        await self.recover()
                
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")
                schedule_exception_report(
                    "database.health_monitor",
                    e,
                )
            
            await asyncio.sleep(self.check_interval)

