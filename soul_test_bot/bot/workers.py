import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database.repository.user as db_user


async def refresh_requests():
    try:
        await db_user.refresh_requests()
    except:
        pass

async def schedule_():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_requests, 'cron', hour=1, minute=0)
    scheduler.start()

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
