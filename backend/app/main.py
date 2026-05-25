import sys
import os

from pathlib import Path

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import uvicorn

# Ensure the backend directory is on sys.path so 'app' module is importable
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.config import settings
from app.database import init_db
from app.routes import projects, content, evidence, verification, chat
from app.routes.health import router as health_router
from app.routes.workflow import register_workflow_routes

from app.log_config.logger import setup_logging

logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Verified AI Research Writer API")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down Verified AI Research Writer API")


app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    lifespan=lifespan,
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors and log the detailed error for debugging.
    This is especially useful for finding mismatches between frontend payloads and pydantic models.
    """
    error_details = exc.errors()
    logger.error(f"Validation error for {request.method} {request.url.path}: {error_details}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_details,
            "body": exc.body
        },
    )

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

register_workflow_routes(projects.router)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(projects.router, prefix=settings.api_v1_prefix)
app.include_router(content.router, prefix=settings.api_v1_prefix)
app.include_router(evidence.router, prefix=settings.api_v1_prefix)
app.include_router(verification.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)


_static_dir = Path(__file__).resolve().parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def api_docs_page():
    index_path = _static_dir / "index.html"
    if index_path.exists():
        html = index_path.read_text(encoding="utf-8")
        return HTMLResponse(content=html)
    return HTMLResponse(content="<h1>Verified AI Research Writer API</h1><p>See <a href='/docs'>/docs</a> for Swagger UI.</p>")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.project_version}


if __name__ == "__main__":
    import uvicorn
    _wf_counts = len([r for r in app.routes if hasattr(r, 'path') and 'workflow' in r.path])
    print(f"SERVER START: app has {_wf_counts} workflow routes out of {len([r for r in app.routes if hasattr(r, 'path')])} total", flush=True)
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
    )
