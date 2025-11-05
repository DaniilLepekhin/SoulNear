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


def with_db_retry(
    max_retries: int = 3,
    base_delay: float = 0.5,
    backoff_multiplier: float = 2.0,
    log_failures: bool = True
):
    """
    Decorator that retries database operations on connection failures.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        backoff_multiplier: Multiplier for exponential backoff
        log_failures: Whether to log retry attempts
    
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
            
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if error is retriable
                    if not is_retriable_error(e):
                        # Not a connection issue - fail immediately
                        logger.error(f"❌ Non-retriable error in {func.__name__}: {e}")
                        raise
                    
                    # Last attempt - don't retry anymore
                    if attempt == max_retries:
                        if log_failures:
                            logger.error(
                                f"❌ {func.__name__} failed after {max_retries} retries: {e}"
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
        """Perform a simple health check query."""
        try:
            from sqlalchemy import text
            async with self.db_manager.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    async def recover(self) -> bool:
        """Attempt to recover database connection."""
        logger.warning("🔄 Attempting database recovery...")
        try:
            await self.db_manager.ensure_ready()
            logger.info("✅ Database recovered successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database recovery failed: {e}")
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
            
            await asyncio.sleep(self.check_interval)

