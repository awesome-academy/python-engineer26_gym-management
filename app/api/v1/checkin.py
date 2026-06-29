from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models import User
from app.schemas import CheckInResponse, CreateCheckInRequest, PaginatedResponse
from app.services.checkin import CheckInService

router = APIRouter(prefix="/checkins", tags=["Check-ins"])


@router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    payload: CreateCheckInRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CheckInResponse:
    return await CheckInService(session).create(payload)


@router.get("/history", response_model=PaginatedResponse[CheckInResponse])
async def get_checkin_history(
    member_id: Annotated[str, Query(..., description="Member ID")],
    from_date: Annotated[
        Optional[str], Query(description="Start date (YYYY-MM-DD)")
    ] = None,
    to_date: Annotated[
        Optional[str], Query(description="End date (YYYY-MM-DD)")
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[CheckInResponse]:
    items, total = await CheckInService(session).get_history(
        member_id=member_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
    )
