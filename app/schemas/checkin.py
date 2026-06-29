from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CheckInBase(BaseModel):
    member_id: str
    checked_in_at: datetime
    note: Optional[str] = None


class CreateCheckInRequest(CheckInBase):
    pass


class CheckInResponse(CheckInBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CheckInHistoryQuery(BaseModel):
    member_id: str = Field(..., description="Member ID to filter by")
    from_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD format)")
    to_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD format)")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
