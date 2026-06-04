import asyncio
import sys
import os
import uuid
import time

from datetime import datetime
from pathlib import Path

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete

from app.config import settings
from app.database import init_db, dispose_engine, async_session_factory, validate_environment
from app.models.content_version import ContentLock
from app.routes import projects, content, evidence, verification, chat, enhance, ws, sse, sse_agents
from app.api.pipeline import router as pipeline_router
from app.routes.health import router as health_router, HealthResponse
from app.routes.workflow import register_workflow_routes
from app.log_config.logger import setup_logging, set_correlation_id
from app.utils.datetime_utils import utc_now

logger = setup_logging(__name__)

_CONTENT_LOCK_CLEANUP_INTERVAL = 60.0  # seconds


async def _cleanup_expired_locks():
    """Periodically clean up expired content locks."""
    missing_table = False
    while True:
        try:
            await asyncio.sleep(_CONTENT_LOCK_CLEANUP_INTERVAL)
            async with async_session_factory() as session:
                now = utc_now()
                stmt = delete(ContentLock).where(ContentLock.expires_at < now)
                result = await session.execute(stmt)
                await session.commit()
                if result.rowcount > 0:
                    logger.info("Cleaned up %d expired content locks", result.rowcount)
            missing_table = False
        except asyncio.CancelledError:
            break
        except Exception as e:
            err_str = str(e)
            if "does not exist" in err_str and not missing_table:
                logger.warning("Content lock table not yet created; skipping cleanup. %s", err_str.split("\n")[0])
                missing_table = True
            elif "does not exist" not in err_str:
                logger.warning("Content lock cleanup error: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Verified AI Research Writer API")
    validate_environment()
    await init_db()
    logger.info("Database initialized")
    cleanup_task = asyncio.create_task(_cleanup_expired_locks())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Shutting down Verified AI Research Writer API")
    await dispose_engine()


app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request tracing middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(cid)
    start = time.time()
    response = await call_next(request)
    elapsed_ms = round((time.time() - start) * 1000, 2)
    response.headers["X-Correlation-ID"] = cid
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
    logger.info(
        "%s %s -> %s (%.2fms)",
        request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Sanitize error details to ensure they are JSON serializable.
    # Pydantic v2 errors can contain non-serializable objects (like ValueErrors) in 'ctx'.
    raw_errors = exc.errors()
    error_details = []
    for error in raw_errors:
        sanitized = error.copy()
        if "ctx" in sanitized:
            ctx = sanitized["ctx"]
            new_ctx = {}
            for k, v in ctx.items():
                if isinstance(v, (str, int, float, bool, type(None))):
                    new_ctx[k] = v
                else:
                    new_ctx[k] = str(v)
            sanitized["ctx"] = new_ctx
        error_details.append(sanitized)

    logger.error(
        "Validation error for %s %s: %s",
        request.method, request.url.path, error_details,
        extra={"body": str(exc.body)},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details, "body": str(exc.body)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled error for %s %s: %s",
        request.method, request.url.path, str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routes
# ---------------------------------------------------------------------------
register_workflow_routes(projects.router)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(projects.router, prefix=settings.api_v1_prefix)
app.include_router(content.router, prefix=settings.api_v1_prefix)
app.include_router(evidence.router, prefix=settings.api_v1_prefix)
app.include_router(verification.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)
app.include_router(enhance.router, prefix=settings.api_v1_prefix)
app.include_router(ws.router)
app.include_router(sse_agents.router, prefix=settings.api_v1_prefix)
app.include_router(sse.router, prefix=settings.api_v1_prefix)

# ---------------------------------------------------------------------------
# V3 Pipeline routes (new typed architecture)
# ---------------------------------------------------------------------------
app.include_router(pipeline_router, prefix=settings.api_v1_prefix)

# ---------------------------------------------------------------------------
# Static files & root endpoint
# ---------------------------------------------------------------------------
_static_dir = Path(__file__).resolve().parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def api_docs_page():
    index_path = _static_dir / "index.html"
    if index_path.exists():
        html = index_path.read_text(encoding="utf-8")
        return HTMLResponse(content=html)
    return HTMLResponse(
        content="<h1>Verified AI Research Writer API</h1><p>See <a href='/docs'>/docs</a> for Swagger UI.</p>"
    )


# ---------------------------------------------------------------------------
# Health checks (additional top-level shortcut)
# ---------------------------------------------------------------------------
from app.routes.health import HealthResponse


@app.get("/health", response_model=HealthResponse, include_in_schema=False)
async def health_check_root():
    return HealthResponse(status="healthy", version=settings.project_version, database="connected")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
