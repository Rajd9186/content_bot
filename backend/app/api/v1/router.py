from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints.orchestration import router as orchestration_router
from app.domains.workflow.api import router as workflow_router
from app.domains.content.api import router as content_router

api_router = APIRouter()

api_router.include_router(
    health.router,
    prefix="/health",
)
api_router.include_router(orchestration_router, prefix="/orchestration")
api_router.include_router(workflow_router, prefix="/workflows")
api_router.include_router(content_router, prefix="/content")
