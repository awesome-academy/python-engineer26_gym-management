from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PaginatedResponse, PaginationQuery
from app.schemas.subscription import SubscriptionResponse


def _validate_phone(v: str | None) -> str | None:
    if v is None:
        return v
    if not v or not v.strip():
        raise ValueError("Phone cannot be empty")
    v = v.strip()
    # Allow: all digits OR + followed by digits only
    if not re.match(r"^\+?\d+$", v):
        raise ValueError("Phone must contain only digits, optionally prefixed with '+'")
    return v


def _validate_full_name(v: str | None) -> str | None:
    if v is None:
        return v
    if not v or not v.strip():
        raise ValueError("Full name cannot be empty")
    return v.strip()


class CreateMemberRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    full_name: str = Field(..., min_length=1, max_length=100, description="Full name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, max_length=10, description="Gender")
    avatar_url: Optional[str] = Field(None, max_length=255, description="Avatar URL")
    note: Optional[str] = Field(None, description="Note about member")

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        return _validate_phone(v)

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        return _validate_full_name(v)


class UpdateMemberRequest(BaseModel):
    phone: Optional[str] = Field(
        None, min_length=10, max_length=20, description="Phone number"
    )
    full_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Full name"
    )
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, max_length=10, description="Gender")
    avatar_url: Optional[str] = Field(None, max_length=255, description="Avatar URL")
    note: Optional[str] = Field(None, description="Note about member")

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        return _validate_phone(v)

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        return _validate_full_name(v)


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    phone: str
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MemberDetailResponse(MemberResponse):
    subscription_history: PaginatedResponse[SubscriptionResponse] = Field(
        default_factory=lambda: PaginatedResponse[SubscriptionResponse](
            items=[], total=0, page=1, limit=10
        )
    )


class MemberListQuery(PaginationQuery):
    phone: str = Field(default="", max_length=20, description="Search by phone")
    full_name: str = Field(
        default="", max_length=100, description="Search by full name"
    )

    @field_validator("phone", "full_name")
    @classmethod
    def normalize_search_fields(cls, v: str) -> str:
        return v.strip()
