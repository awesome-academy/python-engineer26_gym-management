from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.repositories import CheckInRepository, MemberRepository, SubscriptionRepository
from app.schemas import CheckInResponse, CreateCheckInRequest


class CheckInService:
    def __init__(self, session: AsyncSession):
        self._repo = CheckInRepository(session)
        self._member_repo = MemberRepository(session)
        self._subscription_repo = SubscriptionRepository(session)

    async def create(self, payload: CreateCheckInRequest) -> CheckInResponse:
        member = await self._member_repo.get_by_id(payload.member_id)
        if not member:
            raise NotFoundException("Member not found")

        check_date = payload.checked_in_at.date()

        subscription = await self._subscription_repo.get_active_subscription(
            member_id=payload.member_id,
            check_date=check_date,
        )

        if not subscription:
            raise NotFoundException(
                "Member has no active subscription on the given date"
            )

        checkin = await self._repo.create(**payload.model_dump())
        return CheckInResponse.model_validate(checkin)

    async def get_history(
        self,
        member_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[CheckInResponse], int]:
        from_date_obj = None
        to_date_obj = None

        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValidationException(
                    "Invalid from_date format. Use YYYY-MM-DD",
                    details={"from_date": from_date},
                ) from exc

        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValidationException(
                    "Invalid to_date format. Use YYYY-MM-DD",
                    details={"to_date": to_date},
                ) from exc

        skip = (page - 1) * limit
        checkins, total = await self._repo.get_history(
            member_id=member_id,
            from_date=from_date_obj,
            to_date=to_date_obj,
            skip=skip,
            limit=limit,
        )

        return (
            [CheckInResponse.model_validate(c) for c in checkins],
            total,
        )
