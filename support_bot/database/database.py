import logging

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_DB, POSTGRES_PORT
from database.models import Base

log = logging.getLogger('database.engine')

engine = create_async_engine(
    URL(
        drivername='postgresql+asyncpg',
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        query={},

    ),
    future=True,
    pool_size=20,
    max_overflow=10
)

db = async_sessionmaker(engine, expire_on_commit=False)

async def create_tables() -> None:
    global engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
