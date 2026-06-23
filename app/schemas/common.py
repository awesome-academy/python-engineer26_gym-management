from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationQuery(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)
    page: int = Field(default=1, ge=1)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
