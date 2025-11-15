from __future__ import annotations

import logging

from aiogram import Dispatcher
from aiogram.types import ErrorEvent

from bot.services.error_notifier import report_exception

logger = logging.getLogger(__name__)


async def _on_dispatcher_error(event: ErrorEvent) -> bool:
    exception = event.exception

    update_id = getattr(event.update, "update_id", "unknown")

    if exception:
        logger.exception(
            "Unhandled dispatcher error for update %s",
            update_id,
            exc_info=exception,
        )
    else:
        logger.error("Unhandled dispatcher error for update %s (no exception instance)", update_id)

    await report_exception(
        "dispatcher.error",
        exception or "Unknown error",
        event=event,
    )

    # Returning True prevents aiogram from logging duplicate stack traces
    return True


def register_error_handlers(dp: Dispatcher) -> None:
    dp.errors.register(_on_dispatcher_error)


