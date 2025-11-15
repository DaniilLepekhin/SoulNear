import asyncio
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database.repository.user as db_user
from bot.handlers.user.retention import send_next_retention_message
from bot.handlers.user.broadcast import send_next_broadcast_message


async def refresh_requests():
    try:
        await db_user.refresh_requests()
    except:
        pass


async def check_retention_messages():
    """
    Проверять каждый день кому отправить retention сообщения (допродажи).
    Интервал: 2 дня между сообщениями.
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

            # Пропустить если еще не начали retention (должен быть установлен last_retention_sent)
            if user.last_retention_sent is None:
                continue

            # Проверить интервал - 2 дня между сообщениями
            days_passed = (datetime.now() - user.last_retention_sent).days
            if days_passed >= 2:
                await send_next_retention_message(user.user_id)

    except Exception as e:
        print(f"Ошибка в check_retention_messages: {e}")


async def check_broadcast_messages():
    """
    Проверять каждый день кому отправить общую рассылку.
    Интервал: 1 день между сообщениями.
    Отправляется ВСЕМ пользователям (даже с подпиской).
    """
    try:
        # Получить всех активных пользователей
        users = await db_user.get_all_for_broadcast()

        for user in users:
            # Проверить интервал
            if user.last_broadcast_sent:
                days_passed = (datetime.now() - user.last_broadcast_sent).days
                if days_passed >= 1:  # 1 день между сообщениями
                    await send_next_broadcast_message(user.user_id)
            else:
                # Первое сообщение - отправить через 1 день после регистрации
                days_since_reg = (datetime.now() - user.reg_date).days
                if days_since_reg >= 1:
                    await send_next_broadcast_message(user.user_id)

    except Exception as e:
        print(f"Ошибка в check_broadcast_messages: {e}")


async def schedule_():
    scheduler = AsyncIOScheduler()

    # Обновление запросов в 1:00 UTC (4:00 MSK)
    scheduler.add_job(refresh_requests, 'cron', hour=1, minute=0)

    # Проверка retention сообщений каждый день в 6:00 UTC (9:00 MSK)
    scheduler.add_job(check_retention_messages, 'cron', hour=6, minute=0)

    # Проверка broadcast сообщений каждый день в 6:00 UTC (9:00 MSK)
    scheduler.add_job(check_broadcast_messages, 'cron', hour=6, minute=0)

    scheduler.start()

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
