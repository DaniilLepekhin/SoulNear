import asyncio
import logging
from bot.loader import bot
from bot.middlewares.events import EventsMiddleware
from bot.workers import schedule_


async def main():
    await bot.delete_webhook(drop_pending_updates=False)
    from bot.handlers import dp

    dp.message.middleware(EventsMiddleware())
    dp.callback_query.middleware(EventsMiddleware())

    from database.database import create_tables
    await create_tables()
    asyncio.create_task(schedule_())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
