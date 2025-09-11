from sqlalchemy import select
from database.database import db
from database.models.user import User


async def is_exist(user_id) -> bool:
    async with db.begin() as session:
        result = await session.scalar(select(User).where(User.user_id == user_id))

        return bool(result)


async def new(user_id, topic_id) -> None:
    async with db.begin() as session:
        session.add(User(user_id=user_id, topic_id=topic_id))

        await session.commit()


async def get(user_id) -> User:
    async with db.begin() as session:
        result = await session.scalar(select(User).where(User.user_id == user_id))

        return result


async def get_by_topic(topic_id) -> User:
    async with db.begin() as session:
        result = await session.scalar(select(User).where(User.topic_id == topic_id))

        return result
