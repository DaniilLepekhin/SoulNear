import asyncio
import logging
from aiogram.methods import DeleteWebhook
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backup import backup_bd
from functions import send_message_to_admins
from loader import bot


async def _schedule():
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        backup_bd,
        IntervalTrigger(hours=3),
        id='periodic_task',
        replace_existing=True
    )

    scheduler.start()


async def startup():
    await send_message_to_admins('Бот/Сервер включен')
    asyncio.get_event_loop().create_task(_schedule())


async def shutdown():
    await send_message_to_admins('Бот/Сервер выключен')


async def main():
    from callbacks import dp
    logging.basicConfig(level=logging.INFO)

    try:
        await bot(DeleteWebhook(drop_pending_updates=True))
        await startup()

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )

    finally:
        await shutdown()
        await dp.fsm.storage.close()


if __name__ == '__main__':
    asyncio.run(main())
