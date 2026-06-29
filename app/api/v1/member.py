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
    MemberDetailResponse,
    MemberResponse,
)
from app.services.member import MemberService

router = APIRouter(prefix="/members", tags=["Members"])


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    payload: CreateMemberRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MemberResponse:
    return await MemberService(session).create(payload)


@router.get("/{member_id}", response_model=MemberDetailResponse)
async def get_member(
    member_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MemberDetailResponse:
    return await MemberService(session).get(member_id, page=page, limit=limit)


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
