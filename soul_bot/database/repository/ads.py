import random
import string

from sqlalchemy import select, update
from database.database import db
from database.models.ads import Ad


async def generate_link():
    while True:
        alph = list(string.ascii_lowercase)
        random.shuffle(alph)
        link = alph[:10]
        link = ''.join(link)

        if not await get_by_link(link):
            break

    return link


async def new(name, cost) -> str:
    link = await generate_link()

    async with db() as session:
        session.add(Ad(name=name,
                        link=link,
                        cost=cost))
        await session.commit()

    return link


async def get(ad_id: int) -> Ad | None:
    async with db() as session:
        result = await session.scalar(select(Ad).
                                      where(Ad.id == ad_id))
        return result


async def get_all() -> list[Ad] | None:
    async with db() as session:
        result = await session.scalars(select(Ad).order_by(Ad.create_date.asc()))
        return result.all()


async def get_by_link(link: str) -> Ad | None:
    async with db() as session:
        result = await session.scalar(select(Ad).
                                      where(Ad.link == link))
        return result


async def increment_users(ad_id: int) -> None:
    async with db() as session:
        await session.execute(update(Ad).
                              where(Ad.id == ad_id).
                              values(users=Ad.users + 1))
        await session.commit()


async def increment_views(ad_id: int) -> None:
    async with db() as session:
        await session.execute(update(Ad).
                              where(Ad.id == ad_id).
                              values(views=Ad.views + 1))
        await session.commit()


async def update_earn(link: str, value: int) -> None:
    async with db() as session:
        await session.execute(update(Ad).
                              where(Ad.link == link).
                              values(earn=Ad.earn + value))
        await session.commit()

