import asyncio
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database.repository.user as db_user
from bot.handlers.user.retention import send_next_retention_message


async def refresh_requests():
    try:
        await db_user.refresh_requests()
    except:
        pass


async def check_retention_messages():
    """
    Проверять каждый день кому отправить retention сообщения.
    Интервал: 2-3 дня между сообщениями.
    """
    try:
        # Получить всех пользователей для retention
        users = await db_user.get_all_for_retention()

        for user in users:
            # Пропустить если есть подписка
            if user.sub_date >= datetime.now():
                continue

            # Пропустить если пауза
            if user.retention_paused:
                continue

            # Пропустить если еще не начали retention
            if user.last_retention_message == 0 and user.last_retention_sent is None:
                continue

            # Проверить интервал
            if user.last_retention_sent:
                days_passed = (datetime.now() - user.last_retention_sent).days
                if days_passed >= 2:  # 2 дня между сообщениями
                    await send_next_retention_message(user.user_id)
            else:
                # Первое сообщение - отправить сразу
                await send_next_retention_message(user.user_id)

    except Exception as e:
        print(f"Ошибка в check_retention_messages: {e}")


async def schedule_():
    scheduler = AsyncIOScheduler()

    # Обновление запросов в 1:00
    scheduler.add_job(refresh_requests, 'cron', hour=1, minute=0)

    # Проверка retention сообщений каждый день в 10:00
    scheduler.add_job(check_retention_messages, 'cron', hour=10, minute=0)

    scheduler.start()

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
