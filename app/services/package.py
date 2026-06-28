from __future__ import annotations

from app.core.enum import UserRole
from app.models.user import User
from app.repositories.package import PackageRepository
from app.schemas.common import PaginatedResponse
from app.schemas.package import PackageCreate, PackageResponse, PackageUpdate
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException


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

    async def get_by_id(self, package_id: str) -> PackageResponse:
        package = await self._repo.get_by_id(package_id)
        if not package:
            raise NotFoundException("Package not found")
        return PackageResponse.model_validate(package, from_attributes=True)

    async def update(
        self, current_user: User, package_id: str, payload: PackageUpdate
    ) -> PackageResponse:
        if not current_user.role == UserRole.ADMIN:
            raise ForbiddenException("Only admin users can update packages")

        package = await self._repo.get_by_id(package_id)
        if not package:
            raise NotFoundException("Package not found")

        update_data: dict[str, object] = {}
        if payload.name is not None:
            update_data["name"] = payload.name
        if payload.description is not None:
            update_data["description"] = payload.description
        if payload.price is not None:
            update_data["price"] = payload.price
        if payload.duration is not None:
            update_data["duration_days"] = payload.duration
        if payload.is_active is not None:
            update_data["is_active"] = payload.is_active

        if update_data:
            package = await self._repo.update(package, **update_data)

        return PackageResponse.model_validate(package, from_attributes=True)

    async def delete(self, current_user: User, package_id: str) -> None:
        if not current_user.role == UserRole.ADMIN:
            raise ForbiddenException("Only admin users can delete packages")

        package = await self._repo.get_by_id(package_id)
        if not package:
            raise NotFoundException("Package not found")

        await self._repo.delete(package)
