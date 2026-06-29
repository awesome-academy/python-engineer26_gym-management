from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Member
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class MemberRepository(BaseRepository[Member]):
    model = Member

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_with_subscription_history(
        self,
        member_id: str,
        *,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[Member | None, list[Subscription], int]:
        member_stmt = select(self.model).where(
            (self.model.id == member_id) & (self.model.deleted_at.is_(None))
        )
        member_result = await self.session.execute(member_stmt)
        member = member_result.scalars().first()

        if not member:
            return None, [], 0

        subscription_filters = [
            Subscription.member_id == member_id,
            Subscription.deleted_at.is_(None),
        ]

        count_stmt = (
            select(func.count()).select_from(Subscription).where(*subscription_filters)
        )
        total = (await self.session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * limit
        subscription_stmt = (
            select(Subscription)
            .where(*subscription_filters)
            .options(joinedload(Subscription.package))
            .order_by(desc(Subscription.created_at))
            .offset(offset)
            .limit(limit)
        )
        subscriptions = (
            (await self.session.execute(subscription_stmt)).scalars().unique().all()
        )

        return member, list(subscriptions), total
