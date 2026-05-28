from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    code: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: List[ErrorDetail] = Field(default_factory=list)


class MetaResponse(BaseModel):
    requestId: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlationId: str
    version: str = "1.0.0"


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[ErrorResponse] = None
    meta: MetaResponse


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    pageSize: int
    totalPages: int
