from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _generate_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(
        primary_key=True, default=_generate_uuid, unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(default=None, nullable=True)
