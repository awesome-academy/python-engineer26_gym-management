from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PaginationQuery


class PackageCreate(BaseModel):
    name: str
    description: str
    price: float
    duration: int

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        if len(v) > 500:
            raise ValueError("Description cannot exceed 500 characters")
        return v.strip()

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        if v > 1000000000:
            raise ValueError("Price cannot exceed 1,000,000,000")
        return v

    @field_validator("duration")
    @classmethod
    def duration_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Duration must be greater than 0")
        if v > 365:
            raise ValueError("Duration cannot exceed 365 days")
        return v


class PackageUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    duration: int | None = Field(default=None, validation_alias="duration_days")
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        if len(v) > 500:
            raise ValueError("Description cannot exceed 500 characters")
        return v.strip()

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        if v > 1000000000:
            raise ValueError("Price cannot exceed 1,000,000,000")
        return v

    @field_validator("duration")
    @classmethod
    def duration_positive(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("Duration must be greater than 0")
        if v > 365:
            raise ValueError("Duration cannot exceed 365 days")
        return v

    @field_validator("is_active")
    @classmethod
    def is_active_not_none(cls, v: bool | None) -> bool | None:
        if v is None:
            raise ValueError("is_active cannot be None")
        return v


class PackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    price: float
    duration: int = Field(validation_alias="duration_days")
    is_active: bool = True
    deleted_at: datetime | None = None


class PackageListQuery(PaginationQuery):
    name: str = Field(default="", max_length=100)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip()
