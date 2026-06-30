from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import CREATE_MEMBER_REQUEST_EXAMPLES, responses_for
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.member import (
    CreateMemberRequest,
    UpdateMemberRequest,
    MemberListQuery,
    MemberDetailResponse,
    MemberResponse,
)
from app.services.member import MemberService

router = APIRouter(prefix="/members", tags=["Members"])


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a member",
    description="Register a new gym member profile.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def create_member(
    payload: CreateMemberRequest = Body(
        ..., openapi_examples=CREATE_MEMBER_REQUEST_EXAMPLES
    ),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MemberResponse:
    return await MemberService(session).create(payload)


@router.get(
    "/{member_id}",
    response_model=MemberDetailResponse,
    summary="Get member details",
    description="Return member profile details together with paginated related data.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def get_member(
    member_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MemberDetailResponse:
    return await MemberService(session).get(member_id, page=page, limit=limit)


@router.put(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Update a member",
    description="Update member profile information.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def update_member(
    member_id: str,
    payload: UpdateMemberRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MemberResponse:
    return await MemberService(session).update(member_id, payload)


@router.get(
    "",
    response_model=PaginatedResponse[MemberResponse],
    summary="List members",
    description="Return a paginated list of members with the supported filters.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def get_members(
    query: Annotated[MemberListQuery, Query()],
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[MemberResponse]:
    return await MemberService(session).get_list(query)


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a member",
    description="Remove a member record from the system according to business rules.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def delete_member(
    member_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await MemberService(session).delete(member_id)
