from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.services.subscription import SubscriptionService


def get_subscription_service(
    session: AsyncSession = Depends(get_db),
) -> SubscriptionService:
    return SubscriptionService(session)
