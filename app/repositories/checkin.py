from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin import CheckIn
from app.repositories.base import BaseRepository


class CheckInRepository(BaseRepository[CheckIn]):
    model = CheckIn

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_history(
        self,
        member_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[CheckIn], int]:
        filters = [self.model.member_id == member_id, self.model.deleted_at.is_(None)]
        if from_date:
            from_datetime = datetime.combine(from_date, datetime.min.time())
            filters.append(self.model.checked_in_at >= from_datetime)

        if to_date:
            to_datetime = datetime.combine(to_date, datetime.max.time())
            filters.append(self.model.checked_in_at <= to_datetime)

        count_stmt = select(func.count()).select_from(self.model).where(and_(*filters))
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(self.model)
            .where(and_(*filters))
            .order_by(self.model.checked_in_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total
