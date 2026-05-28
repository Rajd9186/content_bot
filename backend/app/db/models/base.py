from datetime import datetime, timezone

from sqlalchemy import TypeDecorator, JSON
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.orm import DeclarativeBase


class JSONBColumn(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGJSONB())
        return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
