from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateMemberSubscriptionRequest(BaseModel):
    package_id: str = Field(..., min_length=1, description="Package ID")


class MemberSubscriptionResponse(BaseModel):
    id: str
    member_id: str
    package_id: str
    subscription_start_date: datetime
    subscription_end_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
