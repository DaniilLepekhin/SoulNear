from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
from database.models import Base

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
    # ✅ FIX: Add connection pool settings to prevent "connection is closed" errors
    pool_size=20,              # Number of permanent connections
    max_overflow=10,           # Number of additional connections when pool is full
    pool_pre_ping=True,        # Verify connections before using them
    pool_recycle=3600,         # Recycle connections after 1 hour
)

db = async_sessionmaker(engine, expire_on_commit=False)


async def create_tables() -> None:
    global engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
