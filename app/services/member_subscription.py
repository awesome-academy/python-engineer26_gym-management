from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.repositories import (
    MemberSubscriptionRepository,
    MemberRepository,
    PackageRepository,
)
from app.schemas import (
    CreateMemberSubscriptionRequest,
    MemberSubscriptionResponse,
)


class MemberSubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self._subscription_repo = MemberSubscriptionRepository(session)
        self._member_repo = MemberRepository(session)
        self._package_repo = PackageRepository(session)

    async def create(
        self,
        member_id: str,
        payload: CreateMemberSubscriptionRequest,
    ) -> MemberSubscriptionResponse:
        member = await self._member_repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member with id '{member_id}' not found")

        package = await self._package_repo.get_by_id(payload.package_id)
        if not package:
            raise NotFoundException(f"Package with id '{payload.package_id}' not found")
        if not package.is_active:
            raise ConflictException(
                f"Package with id '{payload.package_id}' is not active"
            )

        existing = await self._subscription_repo.get_one(
            {"member_id": member_id, "is_active": True}
        )
        if existing:
            raise ConflictException(
                f"Member '{member_id}' already has an active subscription"
            )

        now = datetime.now(timezone.utc)
        start_date = now
        end_date = now + timedelta(days=package.duration_days)

        try:
            subscription = await self._subscription_repo.create(
                member_id=member_id,
                package_id=payload.package_id,
                subscription_start_date=start_date,
                subscription_end_date=end_date,
                is_active=True,
            )
        except exc.IntegrityError as e:
            await self._subscription_repo.session.rollback()
            raise ConflictException(
                f"Member '{member_id}' already has an active subscription"
            ) from e

        return MemberSubscriptionResponse.model_validate(
            subscription, from_attributes=True
        )
