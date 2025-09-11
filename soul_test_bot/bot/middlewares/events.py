import asyncio

from aiogram import Dispatcher, BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Dict, Any, Callable, Awaitable
import database.repository.statistic_day as db_statistic_day
import database.repository.user as db_user


class EventsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        asyncio.get_event_loop().create_task(db_statistic_day.increment('events'))

        user_id = event.from_user.id
        asyncio.get_event_loop().create_task(db_user.update_active(user_id=user_id))

        return await handler(event, data)
