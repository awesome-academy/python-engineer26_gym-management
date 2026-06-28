from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member_subscription import MemberSubscription
from app.repositories.base import BaseRepository


class MemberSubscriptionRepository(BaseRepository[MemberSubscription]):
    model = MemberSubscription

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
