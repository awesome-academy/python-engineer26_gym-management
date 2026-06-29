from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import AsyncSessionFactory
from app.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)


class SchedulerService:
    _scheduler: AsyncIOScheduler | None = None

    @classmethod
    async def init_scheduler(cls) -> None:
        if cls._scheduler is not None:
            logger.warning("Scheduler is already initialized")
            return

        cls._scheduler = AsyncIOScheduler()

        cls._scheduler.add_job(
            cls._update_expired_subscriptions,
            "cron",
            hour=0,
            minute=0,
            id="update_expired_subscriptions",
            name="Update Expired Subscriptions",
            replace_existing=True,
            misfire_grace_time=60,
        )

        cls._scheduler.start()
        logger.info("Scheduler started with job: update_expired_subscriptions")

    @classmethod
    async def shutdown_scheduler(cls) -> None:
        if cls._scheduler is None:
            return

        cls._scheduler.shutdown(wait=True)
        cls._scheduler = None
        logger.info("Scheduler shutdown")

    @classmethod
    async def _update_expired_subscriptions(cls) -> None:
        logger.info(
            "[SCHEDULER] Starting job: update_expired_subscriptions at %s",
            datetime.now(),
        )

        try:
            async with AsyncSessionFactory() as session:
                service = SubscriptionService(session)
                count = await service.update_expired_subscriptions()
                await session.commit()
                logger.info(
                    "[SCHEDULER] Updated %d expired subscriptions to status EXPIRED",
                    count,
                )

        except Exception as e:
            logger.error(
                "[SCHEDULER] Error updating expired subscriptions: %s",
                str(e),
                exc_info=True,
            )
