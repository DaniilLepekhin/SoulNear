from sqlalchemy import select, update
from database.database import db
from database.models.aiogram_state import Aiogram_state
from database.resilience import with_db_retry


@with_db_retry(max_retries=3)
async def new(user_id: int, state: str | None = None) -> None:
    async with db() as session:
        session.add(Aiogram_state(user_id=user_id, state=state))
        await session.commit()


@with_db_retry(max_retries=3)
async def get(user_id: int) -> Aiogram_state:
    async with db() as session:
        result = await session.execute(select(Aiogram_state).
                                       where(Aiogram_state.user_id == user_id))
        return result.scalar()


@with_db_retry(max_retries=3)
async def update_state(user_id: int, state: str | None) -> None:
    async with db() as session:
        await session.execute(update(Aiogram_state).
                              where(Aiogram_state.user_id == user_id).
                              values(state=state))
        await session.commit()


@with_db_retry(max_retries=3)
async def update_data(user_id: int, data: dict | None) -> None:
    async with db() as session:
        await session.execute(update(Aiogram_state).
                              where(Aiogram_state.user_id == user_id).
                              values(data=data))
        await session.commit()
