from __future__ import annotations

from datetime import date
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import SubscriptionStatus
from app.models import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_overlapping_for_member(
        self,
        member_id: str,
        start_date: date,
        end_date: date,
        exclude_subscription_id: str | None = None,
    ) -> Subscription | None:
        conditions = [
            self.model.deleted_at.is_(None),
            self.model.member_id == member_id,
            self.model.status == SubscriptionStatus.ACTIVE,
            self.model.start_date < end_date,
            self.model.end_date > start_date,
        ]

        if exclude_subscription_id:
            conditions.append(self.model.id != exclude_subscription_id)

        stmt = select(self.model).where(*conditions)

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_subscription(
        self,
        member_id: str,
        check_date: date | None = None,
    ) -> Subscription | None:
        if check_date is None:
            check_date = date.today()

        stmt = select(self.model).where(
            and_(
                self.model.member_id == member_id,
                self.model.status == SubscriptionStatus.ACTIVE,
                self.model.start_date <= check_date,
                self.model.end_date >= check_date,
                self.model.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_expired_subscriptions(self) -> int:
        today = date.today()

        select_stmt = select(self.model).where(
            and_(
                self.model.status != SubscriptionStatus.EXPIRED,
                self.model.end_date < today,
                self.model.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(select_stmt)
        expired_subscriptions = result.scalars().all()

        for subscription in expired_subscriptions:
            subscription.status = SubscriptionStatus.EXPIRED

        await self.session.flush()
        return len(expired_subscriptions)
