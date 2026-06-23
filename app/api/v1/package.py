from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_current_user
from app.dependencies.package import get_package_service
from app.models import User
from app.schemas.common import PaginatedResponse
from app.schemas.package import PackageCreate, PackageListQuery, PackageResponse
from app.services.package import PackageService

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    payload: PackageCreate,
    current_user: User = Depends(get_current_user),
    service: PackageService = Depends(get_package_service),
) -> PackageResponse:
    return await service.create(current_user=current_user, payload=payload)


@router.get("", response_model=PaginatedResponse[PackageResponse])
async def get_package_list(
    query: Annotated[PackageListQuery, Query()],
    service: PackageService = Depends(get_package_service),
) -> PaginatedResponse[PackageResponse]:
    return await service.get_list(
        name=query.name,
        limit=query.limit,
        page=query.page,
    )
