from datetime import datetime, date, timedelta

from sqlalchemy import select, update, func

from database.database import db
from database.models.statistic_day import Statistic_day


async def check_today(today) -> None:
    async with db() as session:
        result = await session.scalar(select(func.count()).
                                      where(Statistic_day.date == today))

        if result == 0:
            session.add(Statistic_day(date=today))
            await session.commit()


async def increment(column, value=1):
    today = date.today()
    await check_today(today)

    async with db() as session:
        match column:
            case 'new_users':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(new_users=Statistic_day.new_users + value))
            case 'return_users':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(return_users=Statistic_day.return_users + value))
            case 'block_users':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(block_users=Statistic_day.new_users + value))
            case 'refs':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(refs=Statistic_day.refs + value))
            case 'ads':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(ads=Statistic_day.ads + value))
            case 'sarafan':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(sarafan=Statistic_day.sarafan + value))
            case 'earn':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(earn=Statistic_day.earn + value))
            case 'good_requests':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(good_requests=Statistic_day.good_requests + value))
            case 'bad_requests':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(bad_requests=Statistic_day.bad_requests + value))
            case 'events':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(events=Statistic_day.events + value))
            case 'assistant':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(assistant=Statistic_day.assistant + value))
            case 'helper':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(helper=Statistic_day.helper + value))
            case 'sleeper':
                await session.execute(update(Statistic_day).
                                      where(Statistic_day.date == today).
                                      values(sleeper=Statistic_day.sleeper + value))

        await session.commit()


async def get_today() -> Statistic_day | None:
    today = date.today()

    async with db() as session:
        result = await session.scalar(select(Statistic_day).
                                      where(Statistic_day.date == today))
        return result


async def get_yesterday() -> Statistic_day | None:
    yesterday = (datetime.now() - timedelta(days=1)).date()

    async with db() as session:
        result = await session.scalar(select(Statistic_day).
                                      where(Statistic_day.date == yesterday))
        return result

