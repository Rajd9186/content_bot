from app.routes.projects import router as projects_router
from app.routes.content import router as content_router
from app.routes.evidence import router as evidence_router
from app.routes.verification import router as verification_router

__all__ = [
    "projects_router",
    "content_router",
    "evidence_router",
    "verification_router",
]
