import asyncio
import logging

from database.database import create_tables
from loader import bot

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger(
    'aiogram.event',
).setLevel(logging.WARNING)

log.info("Starting bot...")


async def main():
    from handlers.user import dp
    await create_tables()

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )

    finally:
        await dp.fsm.storage.close()


if __name__ == '__main__':
    asyncio.run(main())
