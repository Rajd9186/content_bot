from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.errors import ErrorHandlingMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.events.outbox_worker import outbox_worker
from app.infrastructure.janitor.worker import janitor_worker
from app.infrastructure.websocket.manager import connection_manager
from app.orchestration.orchestrator import orchestrator

logger = logging.getLogger(__name__)


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

    logger.info("Orchestration engine initialized (singleton)")
    # TODO: recover incomplete workflows from database on startup
    # Requires UnitOfWork wired into lifespan context once DB is available

    yield

    await outbox_worker.stop()
    await janitor_worker.stop()
    await connection_manager.stop_redis_listener()

    try:
        await redis_client.disconnect()
    except Exception:
        pass
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin) for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID", "X-Process-Time-Ms"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)

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
