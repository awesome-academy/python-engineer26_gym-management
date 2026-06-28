from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core import SubscriptionStatus
from app.schemas.common import PaginationQuery


class CreateSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    member_id: str = Field(..., description="Member ID")
    package_id: str = Field(..., description="Package ID")
    start_date: date = Field(..., description="Subscription start date")
    price: float = Field(..., gt=0, description="Subscription price")


class UpdateSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_id: Optional[str] = Field(None, description="Package ID")
    start_date: Optional[date] = Field(None, description="Subscription start date")
    price: Optional[float] = Field(None, gt=0, description="Subscription price")


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    member_id: str
    package_id: str
    start_date: date
    end_date: date
    status: SubscriptionStatus
    price: float
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SubscriptionListQuery(PaginationQuery):
    start_date: date | None = Field(default=None, description="Filter by start date")
    end_date: date | None = Field(default=None, description="Filter by end date")
    member_id: str = Field(default="", description="Filter by member id")
    status: SubscriptionStatus | None = Field(
        default=None,
        description="Filter by subscription status",
    )
    package_id: str = Field(default="", description="Filter by package id")

    @field_validator("end_date")
    @classmethod
    def end_date_not_before_start_date(cls, v: date | None, info) -> date | None:
        start_date = info.data.get("start_date")
        if v is not None and start_date is not None and v < start_date:
            raise ValueError("End date must be on or after start date")
        return v

    @field_validator("member_id", "package_id")
    @classmethod
    def normalize_ids(cls, v: str) -> str:
        return v.strip()
