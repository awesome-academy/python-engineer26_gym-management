from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_current_user
from app.dependencies.subscription import get_subscription_service
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.subscription import (
    CreateSubscriptionRequest,
    SubscriptionListQuery,
    SubscriptionResponse,
)
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post(
    "", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED
)
async def create_subscription(
    payload: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.create(current_user=current_user, payload=payload)


@router.get("", response_model=PaginatedResponse[SubscriptionResponse])
async def get_subscriptions(
    query: Annotated[SubscriptionListQuery, Query()],
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
) -> PaginatedResponse[SubscriptionResponse]:
    return await service.get_list(query)
