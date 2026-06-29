from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Package
from app.repositories.base import BaseRepository


class PackageRepository(BaseRepository[Package]):
    model = Package

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_active_by_id(self, package_id: str) -> Package | None:
        """Get package by ID with conditions: is_active=True and deleted_at is NULL"""
        stmt = select(self.model).where(
            (self.model.id == package_id)
            & (self.model.is_active.is_(True))
            & (self.model.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
