"""Asynchronous database engine with self-healing capabilities."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from asyncpg import DuplicateDatabaseError, InvalidCatalogNameError
from sqlalchemy import URL, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from config import POSTGRES_DB, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER
from database.models import Base


logger = logging.getLogger(__name__)


def _build_engine(database_name: str) -> AsyncEngine:
    return create_async_engine(
        URL(
            drivername='postgresql+asyncpg',
            username=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=database_name,
            query={},
        ),
        future=True,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


_engine: AsyncEngine = _build_engine(POSTGRES_DB)
engine: AsyncEngine = _engine
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


class DatabaseManager:
    """Encapsulates engine lifecycle with automatic database provisioning."""

    def __init__(self, engine_obj: AsyncEngine, session_factory: async_sessionmaker) -> None:
        self._engine = engine_obj
        self._session_factory = session_factory
        self._lock = asyncio.Lock()

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    async def ensure_ready(self) -> None:
        """Ensure target database exists and is reachable."""

        async with self._lock:
            attempt = 1
            while True:
                try:
                    async with self._engine.connect() as conn:
                        await conn.execute(text('SELECT 1'))
                    return
                except InvalidCatalogNameError:
                    logger.warning("Database '%s' missing, creating...", POSTGRES_DB)
                    await self._create_database()
                    await self._reset_engine()
                except OperationalError as exc:
                    if not self._is_missing_database(exc):
                        raise
                    logger.warning(
                        "Database '%s' missing (OperationalError), creating...",
                        POSTGRES_DB,
                    )
                    await self._create_database()
                    await self._reset_engine()
                attempt += 1
                if attempt > 3:
                    raise RuntimeError(f"Unable to prepare database '{POSTGRES_DB}' after retries")

    def _is_missing_database(self, exc: OperationalError) -> bool:
        origin = getattr(exc, 'orig', None)
        if isinstance(origin, InvalidCatalogNameError):
            return True
        message = str(exc).lower()
        return POSTGRES_DB.lower() in message and 'does not exist' in message

    async def _create_database(self) -> None:
        admin_engine = _build_engine('postgres')
        try:
            async with admin_engine.begin() as conn:
                await conn.execute(text(f'CREATE DATABASE "{POSTGRES_DB}"'))
                logger.info("Created database '%s'", POSTGRES_DB)
        except DuplicateDatabaseError:
            logger.info("Database '%s' already exists", POSTGRES_DB)
        finally:
            await admin_engine.dispose()

    async def _reset_engine(self) -> None:
        global engine

        await self._engine.dispose()
        self._engine = _build_engine(POSTGRES_DB)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)
        engine = self._engine

    @asynccontextmanager
    async def _session_context(self):
        await self.ensure_ready()
        async with self._session_factory() as session:
            yield session

    @asynccontextmanager
    async def _begin_context(self):
        await self.ensure_ready()
        async with self._session_factory().begin() as session:
            yield session

    def __call__(self):
        return self._session_context()

    def begin(self):
        return self._begin_context()


db = DatabaseManager(_engine, _session_factory)


async def create_tables() -> None:
    await db.ensure_ready()

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
