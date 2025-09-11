from typing import List

from sqlalchemy import select, update
from sqlalchemy import delete as delete_
from database.database import db
from database.models.media import Media


async def get(id: int) -> Media:
    async with db.begin() as session:
        result = await session.scalar(select(Media).
                                      where(Media.id == id))
        return result


async def get_all() -> List[Media]:
    async with db.begin() as session:
        result = await session.scalars(select(Media))
        return result.all()


async def get_all_by_category(category_id: int) -> List[Media]:
    async with db.begin() as session:
        result = await session.scalars(select(Media).
                                       where(Media.category_id==category_id).
                                       order_by(Media.position))
        return result.all()


async def new(name: str,
              text: str,
              category_id: int,
              media_type: str,
              media_id: str,
              destination: str) -> None:
    medias = await get_all()

    async with db.begin() as session:
        session.add(Media(name=name,
                          text=text,
                          position=len(medias) + 1,
                          category_id=category_id,
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

    async with db.begin() as session:
        await session.execute(delete_(Media))

        for p in tmp_medias:
            session.add(Media(id=p.id,
                              position=p.position,
                              name=p.name,
                              text=p.text,
                              category_id=p.category_id,
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

    async with db.begin() as session:
        await session.execute(delete_(Media))

        for p in tmp_medias:
            session.add(Media(id=p.id,
                              name=p.name,
                              position=p.position,
                              text=p.text,
                              category_id=p.category_id,
                              media_type=p.media_type,
                              media_id=p.media_id,
                              destination=p.destination
                              ))

        await session.commit()
