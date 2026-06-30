from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.docs import responses_for
from app.dependencies.auth import get_current_user
from app.dependencies.subscription import get_subscription_service
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.subscription import (
    CreateSubscriptionRequest,
    SubscriptionListQuery,
    SubscriptionResponse,
    UpdateSubscriptionRequest,
)
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a subscription",
    description="Create a member subscription from an existing package.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def create_subscription(
    payload: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.create(current_user=current_user, payload=payload)


@router.put(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Update a subscription",
    description="Update subscription data before or during its lifecycle.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def update_subscription(
    subscription_id: str,
    payload: UpdateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.update(
        subscription_id=subscription_id,
        current_user=current_user,
        payload=payload,
    )


@router.post(
    "/{subscription_id}/activate",
    response_model=SubscriptionResponse,
    summary="Activate a subscription",
    description="Activate a pending subscription so the member can start using it.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def activate_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.activate(
        subscription_id=subscription_id,
        current_user=current_user,
    )


@router.post(
    "/{subscription_id}/cancel",
    response_model=SubscriptionResponse,
    summary="Cancel a subscription",
    description="Cancel an active or pending subscription based on business rules.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def cancel_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await service.cancel(
        subscription_id=subscription_id,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=PaginatedResponse[SubscriptionResponse],
    summary="List subscriptions",
    description="Return a paginated list of subscriptions visible to the current user.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def get_subscriptions(
    query: Annotated[SubscriptionListQuery, Query()],
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
) -> PaginatedResponse[SubscriptionResponse]:
    return await service.get_list(query)
