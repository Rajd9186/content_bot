import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.config import settings

logger = logging.getLogger("app.database")


def _build_engine_url() -> str:
    url = settings.database_url
    # If PostgreSQL and no async driver specified, add asyncpg
    if "postgresql" in url and "+" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    return url


def _create_engine() -> AsyncEngine:
    url = _build_engine_url()
    connect_args = {}
    engine_kwargs = {
        "url": url,
        "echo": settings.database_echo or (settings.environment == "development"),
    }

    if "sqlite" in url:
        connect_args["check_same_thread"] = False
        connect_args["timeout"] = settings.database_pool_timeout
        engine_kwargs["connect_args"] = connect_args
    else:
        # PostgreSQL pool configuration
        engine_kwargs["pool_size"] = settings.database_pool_size
        engine_kwargs["max_overflow"] = settings.database_max_overflow
        engine_kwargs["pool_timeout"] = settings.database_pool_timeout
        engine_kwargs["pool_pre_ping"] = settings.database_pool_pre_ping
        engine_kwargs["connect_args"] = connect_args or None
        engine_kwargs["isolation_level"] = "AUTOCOMMIT"

    engine = create_async_engine(**engine_kwargs)
    return engine


engine = _create_engine()
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an AsyncSession with automatic commit/rollback.

    The session is committed on success, rolled back on exception,
    and always closed in the finally block.
    """
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager version of get_session for non-route code."""
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def retry_on_db_failure(
    operation: callable,
    max_retries: int = 3,
    base_delay: float = 0.5,
    backoff: float = 2.0,
) -> any:
    """Retry a database operation with exponential backoff on transient errors.

    Handles SQLite locking errors and PostgreSQL serialization failures.
    """
    from sqlalchemy.exc import OperationalError, IntegrityError

    last_exc = None
    for attempt in range(max_retries):
        try:
            return await operation()
        except (OperationalError, IntegrityError) as e:
            last_exc = e
            error_str = str(e).lower()
            if "locked" in error_str or "deadlock" in error_str or "serialization" in error_str:
                delay = base_delay * (backoff ** attempt)
                logger.warning(
                    "Database transient error (attempt %d/%d): %s. Retrying in %.2fs",
                    attempt + 1, max_retries, e, delay,
                )
                await asyncio.sleep(delay)
                continue
            raise
        except Exception:
            raise
    raise last_exc


async def init_db():
    """Initialize database: create all tables and apply performance pragmas."""
    from sqlalchemy import inspect

    async with engine.begin() as conn:
        # SQLite-specific optimizations
        if "sqlite" in settings.database_url:
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL")
            await conn.exec_driver_sql("PRAGMA busy_timeout=30000")
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON")

        await conn.run_sync(Base.metadata.create_all)

    # Verify tables were created
    async with engine.begin() as conn:
        def _check_tables(sync_conn):
            inspector = inspect(sync_conn)
            tables = inspector.get_table_names()
            logger.info("Database tables: %s", tables)
            return tables
        tables = await conn.run_sync(_check_tables)
        if not tables:
            logger.warning("No tables created — check model imports")


async def dispose_engine():
    """Clean up the engine connection pool on shutdown."""
    await engine.dispose()
    logger.info("Database engine disposed")
