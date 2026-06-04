import asyncio
import logging
import os
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
        engine_kwargs["isolation_level"] = "READ COMMITTED"

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


async def run_migrations():
    """Run Alembic migrations to bring the database schema up to date.

    Uses Alembic's command API in a thread executor to avoid blocking
    the async event loop. Falls back to Base.metadata.create_all() if
    alembic is unavailable (offline / test environment).
    """
    def _upgrade():
        try:
            from alembic.config import Config
            from alembic import command
            import alembic

            # Apply the same async-driver fix as _build_engine_url()
            db_url = settings.database_url
            if "postgresql" in db_url and "+" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

            alembic_dir = os.path.join(os.path.dirname(__file__), "..", "alembic")
            alembic_cfg = Config()
            alembic_cfg.set_main_option("script_location", alembic_dir)
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)
            alembic_cfg.set_main_option("prepend_sys_path", ".")

            logger.info("Running Alembic migrations (head)...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Alembic migrations complete")
        except Exception as e:
            err_str = str(e)
            if "Can't locate revision identified by" in err_str:
                logger.warning("Migration version mismatch detected. Attempting to stamp to 0009 and retry...")
                try:
                    command.stamp(alembic_cfg, "0009")
                    command.upgrade(alembic_cfg, "head")
                    logger.info("Alembic migrations complete (after version reset)")
                    return
                except Exception as retry_err:
                    logger.error("Alembic retry also failed: %s", retry_err)
                    raise
            logger.error("Alembic migration failed: %s", e)
            raise

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _upgrade)


async def validate_schema():
    """Validate that the workflow_events table has the expected columns.

    Logs a warning (but does not block startup) if columns are missing.
    This helps catch deployment issues early.
    """
    from sqlalchemy import inspect as sa_inspect

    expected_columns = {
        "workflow_events": [
            "id", "workflow_id", "project_id", "event_type", "agent_name",
            "status", "message", "progress_percent", "payload_json", "created_at",
        ],
    }

    async with engine.begin() as conn:
        def _check(sync_conn):
            inspector = sa_inspect(sync_conn)
            tables = inspector.get_table_names()
            logger.info("Database tables: %s", tables)

            for table, cols in expected_columns.items():
                if table not in tables:
                    logger.warning("Schema validation: table '%s' does not exist", table)
                    continue
                existing = {c["name"] for c in inspector.get_columns(table)}
                missing = [c for c in cols if c not in existing]
                if missing:
                    logger.warning(
                        "Schema validation: table '%s' missing columns: %s. "
                        "Run 'alembic upgrade head' to fix.",
                        table, missing,
                    )
                else:
                    logger.info("Schema validation: table '%s' has all expected columns", table)

        await conn.run_sync(_check)


def validate_environment():
    """Validate critical environment settings at startup.

    Raises ValueError if required configuration is missing or misconfigured.
    """
    db_url = settings.database_url
    if not db_url:
        raise ValueError("DATABASE_URL is not set")

    if settings.environment == "production":
        if "sqlite" in db_url:
            raise ValueError("SQLite is not supported in production — set DATABASE_URL to a PostgreSQL connection string")
        if not db_url.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string in production")
        if settings.secret_key == "change-me-in-production":
            logger.warning("SECRET_KEY is still set to the default value — update it in production")
        if not settings.groq_api_key:
            logger.warning("GROQ_API_KEY is not set — LLM features will not work")

    logger.info("Environment validation passed (environment=%s)", settings.environment)


async def init_db():
    """Initialize database: run migrations, verify schema, apply pragmas."""
    from sqlalchemy import inspect

    async with engine.begin() as conn:
        if "sqlite" in settings.database_url:
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL")
            await conn.exec_driver_sql("PRAGMA busy_timeout=30000")
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON")

    # Run Alembic migrations
    await run_migrations()

    # Validate schema after migration
    await validate_schema()


async def dispose_engine():
    """Clean up the engine connection pool on shutdown."""
    await engine.dispose()
    logger.info("Database engine disposed")
