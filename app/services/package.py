from __future__ import annotations

from app.core.enum import UserRole
from app.models.user import User
from app.repositories.package import PackageRepository
from app.schemas.common import PaginatedResponse
from app.schemas.package import PackageCreate, PackageResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException


class PackageService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = PackageRepository(session)

    async def create(
        self, current_user: User, payload: PackageCreate
    ) -> PackageResponse:
        if not current_user.role == UserRole.ADMIN:
            raise ForbiddenException("Only admin users can create packages")

        package = await self._repo.create(
            name=payload.name,
            description=payload.description,
            price=payload.price,
            duration_days=payload.duration,
        )

        return PackageResponse.model_validate(package, from_attributes=True)

    async def get_list(
        self,
        name: str = "",
        limit: int = 10,
        page: int = 1,
    ) -> PaginatedResponse[PackageResponse]:
        packages = await self._repo.paginate(
            page=page,
            limit=limit,
            name__ilike=name.strip() or None,
        )

        return PaginatedResponse[PackageResponse](
            items=[
                PackageResponse.model_validate(package, from_attributes=True)
                for package in packages.items
            ],
            total=packages.total,
            page=packages.page,
            limit=packages.limit,
        )
