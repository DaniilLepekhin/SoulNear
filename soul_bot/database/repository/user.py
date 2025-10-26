import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, update, func
from database.database import db
from database.models.user import User
from bot.functions.other import add_months
import database.repository.statistic_day as db_statistic_day


async def new(user_id: int,
              name: str,
              username: str,
              ref: str,
              sub_date: datetime) -> None:
    if ref:
        if ref.isdigit():
            asyncio.get_event_loop().create_task(db_statistic_day.increment('refs'))
        else:
            asyncio.get_event_loop().create_task(db_statistic_day.increment('ads'))
    else:
        asyncio.get_event_loop().create_task(db_statistic_day.increment('sarafan'))

    asyncio.get_event_loop().create_task(db_statistic_day.increment('new_users'))

    async with db() as session:
        session.add(User(user_id=user_id,
                         username=username,
                         name=name,
                         ref=ref,
                         sub_date=sub_date,
                         reg_date=datetime.now()))
        await session.commit()


async def is_exist(user_id: int) -> bool:
    async with db() as session:
        result = await session.scalar(select(User).
                                      where(User.user_id == user_id))
        return bool(result)


async def get(user_id: int) -> User | None:
    async with db() as session:
        result = await session.scalar(select(User).
                                      where(User.user_id == user_id))
        return result


async def get_all() -> list[User]:
    async with db() as session:
        result = await session.scalars(select(User))
        return result.all()


async def get_all_active_users_id() -> list[int]:
    async with db() as session:
        result = await session.scalars(select(User.user_id).
                                       where(User.block_date.is_(None)))
        return result.all()


async def panel() -> (int, int):
    async with db() as session:
        users = await session.scalar(select(func.count(User.user_id)))

        block_ = await session.scalar(select(func.count(User.user_id)).
                                      where(User.block_date.is_not(None)))

        active = await session.scalar(select(func.count(User.user_id)).
                                      where(User.active_date > datetime.now() - timedelta(days=1)))

        return users, block_, active


async def update_active(user_id: int) -> None:
    user = await get(user_id=user_id)

    if user.block_date:
        asyncio.get_event_loop().create_task(db_statistic_day.increment('return_users'))

    async with db() as session:
        await session.execute(update(User).
                              where(User.user_id == user_id).
                              values(active_date=datetime.now(),
                                     block_date=None))
        await session.commit()


async def update_sub_date(user_id: int,
                          months: int = 0,
                          weeks: int = 0,
                          days: int = 0) -> None:
    user = await get(user_id=user_id)

    now = datetime.now()
    sub_date = now if user.sub_date < now else user.sub_date

    sub_date = add_months(sub_date, months)
    sub_date = sub_date + timedelta(weeks=weeks)
    sub_date = sub_date + timedelta(days=days)

    async with db() as session:
        await session.execute(update(User).
                              where(User.user_id == user_id).
                              values(sub_date=sub_date))
        await session.commit()


async def block(user_id: int) -> None:
    asyncio.get_event_loop().create_task(db_statistic_day.increment('block_users'))

    async with db() as session:
        await session.execute(update(User).
                              where(User.user_id == user_id).
                              values(block_date=datetime.now()))
        await session.commit()


async def update_helper_thread(user_id: int, thread_id: str) -> None:
    async with db() as session:
        await session.execute(update(User).
                              where(User.user_id == user_id).
                              values(helper_thread_id=thread_id))
        await session.commit()


async def update_assistant_thread(user_id: int, thread_id: str) -> None:
    async with db() as session:
        await session.execute(update(User).
                              where(User.user_id == user_id).
                              values(assistant_thread_id=thread_id))
        await session.commit()


async def update_sleeper_thread(user_id: int, thread_id: str) -> None:
    async with db() as session:
        await session.execute(update(User).
                              where(User.user_id == user_id).
                              values(sleeper_thread_id=thread_id))
        await session.commit()


async def decrement_requests(user_id: int, assistant: str):
    execute = ''
    match assistant:
        case 'helper':
            execute = update(User). \
                where(User.user_id == user_id). \
                values(helper_requests=User.helper_requests - 1)

        case 'sleeper':
            execute = update(User). \
                where(User.user_id == user_id). \
                values(sleeper_requests=User.sleeper_requests - 1)

        case 'assistant':
            execute = update(User). \
                where(User.user_id == user_id). \
                values(assistant_requests=User.assistant_requests - 1)

    async with db() as session:
        await session.execute(execute)
        await session.commit()


async def refresh_requests():
    async with db() as session:
        await session.execute(update(User).
                              values(helper_requests=10,
                                     sleeper_requests=3,
                                     assistant_requests=11))
        await session.commit()  # ⚠️ FIX: Commit изменений в БД!


async def update_info(user_id: int, real_name: str, age: int, gender: bool) -> None:
    async with db() as session:
        await session.execute(update(User).
                              values(real_name=real_name,
                                     age=age,
                                     gender=gender).
                              where(User.user_id == user_id))
        await session.commit()  # ⚠️ FIX: Commit изменений в БД!
