from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import require_admin
from app.dependencies.package import get_package_service
from app.models import User
from app.schemas.common import PaginatedResponse
from app.schemas.package import PackageCreate, PackageListQuery, PackageResponse, PackageUpdate
from app.services.package import PackageService

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    payload: PackageCreate,
    current_admin: User = Depends(require_admin),
    service: PackageService = Depends(get_package_service),
) -> PackageResponse:
    return await service.create(current_user=current_admin, payload=payload)


@router.get(
    "",
    response_model=PaginatedResponse[PackageResponse],
    response_model_exclude={"items": {"__all__": {"is_active"}}},
)
async def get_package_list(
    query: Annotated[PackageListQuery, Query()],
    service: PackageService = Depends(get_package_service),
) -> PaginatedResponse[PackageResponse]:
    return await service.get_list(
        name=query.name,
        limit=query.limit,
        page=query.page,
    )


@router.get("/{id}", response_model=PackageResponse)
async def get_package(
    id: str,
    service: PackageService = Depends(get_package_service),
) -> PackageResponse:
    return await service.get_by_id(id)


@router.put("/{id}", response_model=PackageResponse)
async def update_package(
    id: str,
    payload: PackageUpdate,
    current_admin: User = Depends(require_admin),
    service: PackageService = Depends(get_package_service),
) -> PackageResponse:
    return await service.update(current_user=current_admin, package_id=id, payload=payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    id: str,
    current_admin: User = Depends(require_admin),
    service: PackageService = Depends(get_package_service),
) -> None:
    await service.delete(current_user=current_admin, package_id=id)
