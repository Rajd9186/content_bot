from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Shared base schema with Pydantic v2 best practices.

    All API schemas should inherit from this to ensure consistent
    from_attributes and populate_by_name behavior.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TimestampSchema(BaseSchema):
    """Adds created_at / updated_at timestamp fields."""
    created_at: datetime
    updated_at: datetime | None = None


class UUIDBaseSchema(BaseSchema):
    """Base schema with a UUID primary key."""
    id: UUID
