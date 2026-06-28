from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.member import (
    CreateMemberRequest,
    UpdateMemberRequest,
    MemberListQuery,
    MemberResponse,
)
from app.schemas.member_subscription import (
    CreateMemberSubscriptionRequest,
    MemberSubscriptionResponse,
)
from app.services.member import MemberService
from app.services.member_subscription import MemberSubscriptionService

router = APIRouter(prefix="/members", tags=["Members"])


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    payload: CreateMemberRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MemberResponse:
    return await MemberService(session).create(payload)


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MemberResponse:
    return await MemberService(session).get(member_id)


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: str,
    payload: UpdateMemberRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MemberResponse:
    return await MemberService(session).update(member_id, payload)


@router.get("", response_model=PaginatedResponse[MemberResponse])
async def get_members(
    query: Annotated[MemberListQuery, Query()],
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[MemberResponse]:
    return await MemberService(session).get_list(query)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await MemberService(session).delete(member_id)


@router.post(
    "/{member_id}/subscription",
    response_model=MemberSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_member_subscription(
    member_id: str,
    payload: CreateMemberSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MemberSubscriptionResponse:
    return await MemberSubscriptionService(session).create(member_id, payload)
