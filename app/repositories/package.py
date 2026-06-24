from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Package
from app.repositories.base import BaseRepository


class PackageRepository(BaseRepository[Package]):
    model = Package

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
