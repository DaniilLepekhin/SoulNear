from typing import List
from sqlalchemy import select
from sqlalchemy import delete as delete_
from database.database import db
from database.models.media_category import Media_category


async def get(id: int) -> Media_category:
    async with db() as session:
        result = await session.scalar(select(Media_category).
                                      where(Media_category.id == id))
        return result


async def get_all() -> List[Media_category]:
    async with db() as session:
        result = await session.scalars(select(Media_category).
                                       order_by(Media_category.position))
        return result.all()


async def get_all_by_type(category: str) -> List[Media_category]:
    async with db() as session:
        result = await session.scalars(select(Media_category).
                                       where(Media_category.category==category).
                                       order_by(Media_category.position))
        return result.all()


async def new(name: str,
              text: str,
              category: str,
              media_type: str,
              media_id: str,
              destination: str) -> None:
    categories = await get_all()

    async with db() as session:
        session.add(Media_category(name=name,
                                   text=text,
                                   category=category,
                                   position=len(categories) + 1,
                                   media_type=media_type,
                                   media_id=media_id,
                                   destination=destination))
        await session.commit()


async def delete(id: int) -> None:
    medias = await get_all()

    tmp_medias = []

    for i, p in enumerate(medias, start=1):
        if id == p.id:
            continue

        p.position = i
        tmp_medias.append(p)

    async with db() as session:
        await session.execute(delete_(Media_category))

        for p in tmp_medias:
            session.add(Media_category(id=p.id,
                                       name=p.name,
                                       text=p.text,
                                       position=p.position,
                                       media_type=p.media_type,
                                       media_id=p.media_id,
                                       destination=p.destination
                                       ))

        await session.commit()


async def update_position(now_position: int, need_position: int) -> None:
    medias = await get_all()

    media = medias[now_position - 1]
    media.position = need_position

    medias.pop(now_position - 1)
    medias.insert(need_position - 1, media)

    tmp_medias = []

    for i, p in enumerate(medias, start=1):
        p.position = i
        tmp_medias.append(p)

    async with db() as session:
        await session.execute(delete_(Media_category))

        for p in tmp_medias:
            session.add(Media_category(id=p.id,
                                       name=p.name,
                                       text=p.text,
                                       category=p.category,
                                       position=p.position,
                                       media_type=p.media_type,
                                       media_id=p.media_id,
                                       destination=p.destination
                                       ))

        await session.commit()
