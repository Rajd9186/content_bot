"""
Content API endpoints.
"""

from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/items")
async def list_content_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all content items."""
    # TODO: Implement content listing
    return {
        "items": [],
        "total": 0,
        "skip": skip,
        "limit": limit
    }
