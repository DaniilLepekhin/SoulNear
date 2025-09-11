# import asyncio
# import logging
#
# from sqlalchemy import URL
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
#
# from app.database.models import Base
# from app.utils.config import DB
# log = logging.getLogger('database.engine')
#
#
# def create_sessionmaker(database: DB) -> async_sessionmaker:
#     """
#     Create an async sessionmaker for the database and create tables if they don't exist.
#
#     :param str database: Postgres database credentials
#     :param bool debug: Debug mode, defaults to False
#     :return async_sessionmaker: Async sessionmaker (sessionmaker with AsyncSession class)
#     """
#
#     engine = create_async_engine(
#         URL(
#             'postgresql+asyncpg',
#             database.user,
#             database.password,
#             database.host,
#             database.port,
#             database.name,
#             query={},
#         ), future=True,
#     )
#     log.info('Connected to database')
#     # await create_tables(engine)
#     return async_sessionmaker(engine, expire_on_commit=False)
#
#
# engine = create_async_engine(
#     URL(
#         drivername='postgresql+asyncpg',
#         username='postgres',
#         password='',
#         host='127.0.0.1',
#         port=5432,
#         database='anime_bot',
#         query={},
#     ), future=True,
# )
#
# db = async_sessionmaker(engine, expire_on_commit=False)
#
#
# async def create_tables(engine: AsyncEngine) -> None:
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
#
# asyncio.run(create_tables(engine))
#
# __all__ = ['db']