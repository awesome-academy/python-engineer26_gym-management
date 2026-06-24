from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.services.package import PackageService


def get_package_service(
    session: AsyncSession = Depends(get_db),
) -> PackageService:
    return PackageService(session)
