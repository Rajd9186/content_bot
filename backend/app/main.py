import sys
import os
import uuid
import time

from pathlib import Path

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, dispose_engine
from app.routes import projects, content, evidence, verification, chat
from app.routes.health import router as health_router
from app.routes.workflow import register_workflow_routes
from app.log_config.logger import setup_logging, set_correlation_id

logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Verified AI Research Writer API")
    await init_db()
    logger.info("Database initialized")
    yield
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
    error_details = exc.errors()
    logger.error(
        "Validation error for %s %s: %s",
        request.method, request.url.path, error_details,
        extra={"body": exc.body},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details, "body": exc.body},
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
    allow_origins=[
        "https://verified-ai-research-writer-frontend.onrender.com",
        "http://localhost:3000",        
        "https://verified-ai-research-writer.onrender.com",
        "null",
    ],
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
# Health checks
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.project_version}


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
