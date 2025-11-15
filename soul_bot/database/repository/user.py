import asyncio
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update as sql_update, func
from database.database import db
from database.models.user import User
from utils.date_helpers import add_months  # ← Fixed circular import!
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

    # ✅ FIX: Check if user exists before accessing attributes
    if user is None:
        return
    
    if user.block_date:
        asyncio.get_event_loop().create_task(db_statistic_day.increment('return_users'))

    async with db() as session:
        await session.execute(sql_update(User).
                              where(User.user_id == user_id).
                              values(active_date=datetime.now(),
                                     block_date=None))
        await session.commit()


async def update_sub_date(user_id: int,
                          months: int = 0,
                          weeks: int = 0,
                          days: int = 0) -> None:
    user = await get(user_id=user_id)
    
    # ✅ FIX: Check if user exists before accessing attributes
    if user is None:
        return

    now = datetime.now()
    sub_date = now if user.sub_date < now else user.sub_date

    sub_date = add_months(sub_date, months)
    sub_date = sub_date + timedelta(weeks=weeks)
    sub_date = sub_date + timedelta(days=days)

    async with db() as session:
        await session.execute(sql_update(User).
                              where(User.user_id == user_id).
                              values(sub_date=sub_date))
        await session.commit()


async def block(user_id: int) -> None:
    asyncio.get_event_loop().create_task(db_statistic_day.increment('block_users'))

    async with db() as session:
        await session.execute(sql_update(User).
                              where(User.user_id == user_id).
                              values(block_date=datetime.now()))
        await session.commit()


async def decrement_requests(user_id: int, assistant: str):
    execute = ''
    match assistant:
        case 'helper':
            execute = sql_update(User). \
                where(User.user_id == user_id). \
                values(helper_requests=User.helper_requests - 1)

        case 'sleeper':
            execute = sql_update(User). \
                where(User.user_id == user_id). \
                values(sleeper_requests=User.sleeper_requests - 1)

        case 'assistant':
            execute = sql_update(User). \
                where(User.user_id == user_id). \
                values(assistant_requests=User.assistant_requests - 1)

    async with db() as session:
        await session.execute(execute)
        await session.commit()


async def refresh_requests():
    async with db() as session:
        await session.execute(sql_update(User).
                              values(helper_requests=10,
                                     sleeper_requests=3,
                                     assistant_requests=11))
        await session.commit()  # ⚠️ FIX: Commit изменений в БД!


async def update_info(user_id: int,
                      real_name: str,
                      age: Optional[int],
                      gender: Optional[bool]) -> None:
    async with db() as session:
        await session.execute(sql_update(User).
                              values(real_name=real_name,
                                     age=age,
                                     gender=gender).
                              where(User.user_id == user_id))
        await session.commit()  # ⚠️ FIX: Commit изменений в БД!


async def update(user_id: int, **kwargs) -> None:
    """
    Universal update method for any user fields.
    Usage: await db_user.update(user_id=123, field1=value1, field2=value2)
    """
    async with db() as session:
        await session.execute(
            sql_update(User).
            where(User.user_id == user_id).
            values(**kwargs)
        )
        await session.commit()


async def get_all_for_retention() -> list[User]:
    """
    Получить всех пользователей которым нужно отправить retention сообщения.
    Условия: free_messages_activated=True, free_messages_count=0, нет подписки
    """
    from datetime import datetime
    async with db() as session:
        result = await session.execute(
            select(User).where(
                User.free_messages_activated == True,
                User.free_messages_count == 0,
                User.sub_date < datetime.now(),
                User.last_retention_message < 5  # Не больше 5 сообщений
            )
        )
        return result.scalars().all()


async def get_all_for_broadcast() -> list[User]:
    """
    Получить всех активных пользователей для общей рассылки.
    Условия: активный пользователь (не заблокирован), не больше 15 сообщений
    """
    async with db() as session:
        result = await session.execute(
            select(User).where(
                User.block_date.is_(None),  # Не заблокирован
                User.last_broadcast_message < 15  # Не больше 15 сообщений
            )
        )
        return result.scalars().all()
