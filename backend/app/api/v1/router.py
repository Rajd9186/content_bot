from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints.metrics import router as metrics_router
from app.api.v1.endpoints.orchestration import router as orchestration_router
from app.api.v1.endpoints.pipeline_api import router as content_pipeline_router
from app.api.v1.endpoints.projects import router as projects_router
from app.core.config import settings
from app.domains.content.api import router as content_router
from app.domains.workflow.api import router as workflow_router

api_router = APIRouter()


@api_router.get("", summary="API root", operation_id="getApiRoot")
async def api_root() -> dict:
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_prefix": settings.API_V1_STR,
        "endpoints": [
            f"{settings.API_V1_STR}/health",
            f"{settings.API_V1_STR}/orchestration",
            f"{settings.API_V1_STR}/content-pipeline",
            f"{settings.API_V1_STR}/workflows",
            f"{settings.API_V1_STR}/content",
        ],
        "docs": f"{settings.API_V1_STR}/docs",
    }


@api_router.get("/info", summary="API info", operation_id="getApiInfo")
async def api_info() -> dict:
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "api_prefix": settings.API_V1_STR,
    }


@api_router.get("/version", summary="API version", operation_id="getApiVersion")
async def api_version() -> dict:
    return {
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
    }


api_router.include_router(
    health.router,
    prefix="/health",
)
api_router.include_router(metrics_router)
api_router.include_router(orchestration_router, prefix="/orchestration")
api_router.include_router(content_pipeline_router, prefix="/content-pipeline")
api_router.include_router(workflow_router, prefix="/workflows")
api_router.include_router(content_router, prefix="/content")
api_router.include_router(projects_router, prefix="")
