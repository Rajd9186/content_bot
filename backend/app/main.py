from __future__ import annotations
# Trigger rebuild 2026-06-03-v2

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from datetime import UTC

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.infrastructure.events.outbox_worker import outbox_worker
from app.infrastructure.janitor.worker import janitor_worker
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.sse.manager import sse_manager
from app.infrastructure.websocket.manager import connection_manager
from app.infrastructure.workers.pipeline_worker import pipeline_worker
from app.infrastructure.workers.recovery_worker import pipeline_recovery_worker
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.errors import ErrorHandlingMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.orchestration.orchestrator import orchestrator

logger = logging.getLogger(__name__)


async def _checkpoint_persister(run) -> None:
    from app.infrastructure.database import async_session_factory
    from app.infrastructure.unit_of_work import UnitOfWork
    try:
        async with async_session_factory() as session:
            uow = UnitOfWork(session)
            await uow.checkpoints.save_checkpoint(
                aggregate_id=run.id,
                aggregate_type="workflow",
                checkpoint_type="workflow_run",
                state=run.model_dump(),
                version=run.version,
            )
            await uow.commit()
    except Exception as e:
        logger.warning("Checkpoint persist failed for workflow %s: %s", run.id, e)


async def _dead_letter_handler(run, stage, error, retries) -> None:
    from datetime import datetime

    from app.infrastructure.database import async_session_factory
    from app.infrastructure.models.telemetry import RetryRecord
    from app.infrastructure.unit_of_work import UnitOfWork
    try:
        async with async_session_factory() as session:
            uow = UnitOfWork(session)
            record = RetryRecord(
                target_type="workflow_stage",
                target_id=run.id,
                attempt_number=retries,
                status="exhausted",
                error_code="STAGE_FAILED",
                error_message=error[:1000] if error else "",
                executed_at=datetime.now(UTC),
            )
            uow.session.add(record)
            await uow.commit()
    except Exception as e:
        logger.warning("Dead letter persist failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info(
        "Application starting",
        extra={"environment": settings.ENVIRONMENT, "version": settings.VERSION},
    )

    if settings.REDIS_URL and settings.REDIS_URL != "redis://localhost:6379":
        try:
            await redis_client.connect()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning("Redis connection failed (non-fatal): %s", e)

    if redis_client._client is not None:
        await outbox_worker.start()
        await janitor_worker.start()
        await connection_manager.start_redis_listener()
        await pipeline_worker.start()
        await pipeline_recovery_worker.start()
        await sse_manager.start()

    try:
        orchestrator._checkpoint_persister = _checkpoint_persister
        orchestrator._retry_manager._dead_letter_fn = _dead_letter_handler
        logger.info("Orchestrator wired with checkpoint persister and dead letter handler")
    except Exception as e:
        logger.warning("Failed to wire orchestrator: %s", e)

    logger.info("Orchestration engine initialized (singleton)")

    from app.infrastructure.workers.recovery_worker import recovery_service
    try:
        recovered = await recovery_service.recover_on_startup()
        if recovered > 0:
            logger.info("Recovered %d incomplete workflows on startup", recovered)
    except Exception as e:
        logger.warning("Startup recovery failed: %s", e)

    yield

    await pipeline_worker.stop()
    await pipeline_recovery_worker.stop()
    await sse_manager.stop()
    await outbox_worker.stop()
    await janitor_worker.stop()
    await connection_manager.stop_redis_listener()

    with suppress(Exception):
        await redis_client.disconnect()
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="AI Content Intelligence Platform API Gateway",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "Platform Engineering",
            "url": "https://github.com/ai-content-intel",
        },
        license_info={
            "name": "Proprietary",
        },
    )

    origins = [str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS]
    if settings.DEBUG and "null" not in origins:
        origins.append("null")
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID", "X-Process-Time-Ms"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "service": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "docs": f"{settings.API_V1_STR}/docs",
                "openapi": f"{settings.API_V1_STR}/openapi.json",
            }
        )

    return app


app = create_app()

