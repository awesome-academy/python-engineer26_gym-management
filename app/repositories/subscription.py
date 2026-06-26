from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
