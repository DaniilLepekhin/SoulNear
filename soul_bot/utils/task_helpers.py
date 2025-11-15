"""
Task utilities для безопасного запуска фоновых задач
"""
import asyncio
import logging
from typing import Coroutine, Any

from bot.services.error_notifier import schedule_exception_report

logger = logging.getLogger(__name__)


def create_safe_task(coro: Coroutine[Any, Any, Any], task_name: str = "background_task") -> asyncio.Task:
    """
    Создать фоновую задачу с обработкой ошибок
    
    Вместо:
        asyncio.create_task(some_async_function())
    
    Используй:
        create_safe_task(some_async_function(), "some_task_name")
    
    Args:
        coro: Корутина для выполнения
        task_name: Имя задачи (для логирования)
        
    Returns:
        asyncio.Task
    """
    async def safe_wrapper():
        try:
            await coro
        except Exception as e:
            logger.error(f"❌ Background task '{task_name}' failed: {e}", exc_info=True)
            schedule_exception_report(
                "background_task",
                e,
                extras={"task_name": task_name},
            )
    
    return asyncio.create_task(safe_wrapper(), name=task_name)

