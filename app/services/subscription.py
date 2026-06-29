from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import SubscriptionStatus
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.user import User
from app.repositories.member import MemberRepository
from app.repositories.package import PackageRepository
from app.repositories.subscription import SubscriptionRepository
from app.schemas.common import PaginatedResponse
from app.schemas.subscription import (
    CreateSubscriptionRequest,
    SubscriptionListQuery,
    SubscriptionResponse,
    UpdateSubscriptionRequest,
)


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SubscriptionRepository(session)
        self._member_repo = MemberRepository(session)
        self._package_repo = PackageRepository(session)

    async def create(
        self,
        current_user: User,
        payload: CreateSubscriptionRequest,
    ) -> SubscriptionResponse:
        member = await self._member_repo.get_by_id(payload.member_id)
        if not member:
            raise NotFoundException(f"Member with id '{payload.member_id}' not found")

        package = await self._package_repo.get_by_id(payload.package_id)
        if not package:
            raise NotFoundException(f"Package with id '{payload.package_id}' not found")

        end_date = self._calculate_end_date(
            start_date=payload.start_date,
            duration_days=package.duration_days,
        )

        await self._ensure_subscription_period_is_available(
            member_id=payload.member_id,
            start_date=payload.start_date,
            end_date=end_date,
        )

        subscription = await self._repo.create(
            member_id=payload.member_id,
            package_id=payload.package_id,
            start_date=payload.start_date,
            end_date=end_date,
            status=SubscriptionStatus.PENDING,
            price=payload.price,
            created_by=current_user.id,
        )

        return SubscriptionResponse.model_validate(subscription, from_attributes=True)

    async def get_list(
        self,
        query: SubscriptionListQuery,
    ) -> PaginatedResponse[SubscriptionResponse]:
        subscriptions = await self._repo.paginate(
            page=query.page,
            limit=query.limit,
            start_date__gte=query.start_date or None,
            end_date__lte=query.end_date or None,
            member_id=query.member_id or None,
            status=query.status.value if query.status else None,
            package_id=query.package_id or None,
        )

        return PaginatedResponse[SubscriptionResponse](
            items=[
                SubscriptionResponse.model_validate(subscription, from_attributes=True)
                for subscription in subscriptions.items
            ],
            total=subscriptions.total,
            page=subscriptions.page,
            limit=subscriptions.limit,
        )

    async def update(
        self,
        subscription_id: str,
        current_user: User,
        payload: UpdateSubscriptionRequest,
    ) -> SubscriptionResponse:
        subscription = await self._repo.get_by_id(subscription_id)
        if not subscription:
            raise NotFoundException(
                f"Subscription with id '{subscription_id}' not found"
            )

        package_id = payload.package_id or subscription.package_id
        package = await self._package_repo.get_by_id(package_id)
        if not package:
            raise NotFoundException(f"Package with id '{package_id}' not found")

        start_date = payload.start_date or subscription.start_date
        end_date = self._calculate_end_date(
            start_date=start_date,
            duration_days=package.duration_days,
        )

        await self._ensure_subscription_period_is_available(
            member_id=subscription.member_id,
            start_date=start_date,
            end_date=end_date,
            exclude_subscription_id=subscription_id,
        )

        update_data = payload.model_dump(exclude_unset=True)
        update_data["package_id"] = package_id
        update_data["start_date"] = start_date
        update_data["end_date"] = end_date
        update_data["updated_by"] = current_user.id

        updated_subscription = await self._repo.update(subscription, **update_data)

        return SubscriptionResponse.model_validate(
            updated_subscription, from_attributes=True
        )

    async def activate(
        self,
        subscription_id: str,
        current_user: User,
    ) -> SubscriptionResponse:
        subscription = await self._repo.get_by_id(subscription_id)
        if not subscription:
            raise NotFoundException(
                f"Subscription with id '{subscription_id}' not found"
            )

        if subscription.status == SubscriptionStatus.ACTIVE:
            raise BadRequestException(
                f"Subscription with id '{subscription_id}' is already active"
            )

        if subscription.status in (
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.EXPIRED,
        ):
            raise BadRequestException(
                f"Subscription with id '{subscription_id}' cannot be activated because it is {subscription.status.value}"
            )

        await self._ensure_subscription_period_is_available(
            member_id=subscription.member_id,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            exclude_subscription_id=subscription_id,
        )

        activated_subscription = await self._repo.update(
            subscription,
            status=SubscriptionStatus.ACTIVE,
            updated_by=current_user.id,
        )

        return SubscriptionResponse.model_validate(
            activated_subscription,
            from_attributes=True,
        )

    async def cancel(
        self,
        subscription_id: str,
        current_user: User,
    ) -> SubscriptionResponse:
        subscription = await self._repo.get_by_id(subscription_id)
        if not subscription:
            raise NotFoundException(
                f"Subscription with id '{subscription_id}' not found"
            )

        if subscription.status == SubscriptionStatus.CANCELLED:
            raise BadRequestException(
                f"Subscription with id '{subscription_id}' is already cancelled"
            )

        cancelled_subscription = await self._repo.update(
            subscription,
            status=SubscriptionStatus.CANCELLED,
            updated_by=current_user.id,
        )

        return SubscriptionResponse.model_validate(
            cancelled_subscription,
            from_attributes=True,
        )

    async def _ensure_subscription_period_is_available(
        self,
        *,
        member_id: str,
        start_date: date,
        end_date: date,
        exclude_subscription_id: str | None = None,
    ) -> None:
        overlapping_subscription = await self._repo.get_overlapping_for_member(
            member_id=member_id,
            start_date=start_date,
            end_date=end_date,
            exclude_subscription_id=exclude_subscription_id,
        )
        if overlapping_subscription:
            raise BadRequestException(
                f"Member with id '{member_id}' already has a subscription covering the selected period"
            )

    def _calculate_end_date(self, start_date: date, duration_days: int) -> date:
        return start_date + timedelta(days=duration_days)

    async def update_expired_subscriptions(self) -> int:
        return await self._repo.update_expired_subscriptions()
