from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.member import MemberRepository
from app.repositories.package import PackageRepository
from app.repositories.subscription import SubscriptionRepository
from app.repositories.user import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.subscription import (
    CreateSubscriptionRequest,
    SubscriptionListQuery,
    SubscriptionResponse,
)


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SubscriptionRepository(session)
        self._member_repo = MemberRepository(session)
        self._package_repo = PackageRepository(session)
        self._user_repo = UserRepository(session)

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

        if payload.sold_by:
            sold_by_user = await self._user_repo.get_by_id(payload.sold_by)
            if not sold_by_user:
                raise NotFoundException(
                    f"User with id '{payload.sold_by}' not found for sold_by"
                )

        # TODO: Add validation for overlapping subscriptions for the same member and package

        subscription = await self._repo.create(
            member_id=payload.member_id,
            package_id=payload.package_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=payload.status.value,
            price=payload.price,
            created_by=current_user.id,
            sold_by=payload.sold_by,
        )

        return SubscriptionResponse.model_validate(subscription, from_attributes=True)

    async def get_list(
        self,
        query: SubscriptionListQuery,
    ) -> PaginatedResponse[SubscriptionResponse]:
        subscriptions = await self._repo.paginate(
            page=query.page,
            limit=query.limit,
            start_date=query.start_date or None,
            end_date=query.end_date or None,
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
