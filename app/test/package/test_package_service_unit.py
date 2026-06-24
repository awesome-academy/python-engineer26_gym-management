from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import UserRole
from app.core.exceptions import ForbiddenException
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.package import PackageCreate
from app.services.package import PackageService


def _make_user(role: UserRole) -> User:
    return User(
        id="user-1",
        username="tester",
        password_hash="hashed",
        full_name="Test User",
        role=role,
        is_active=True,
    )


def _make_service() -> PackageService:
    return PackageService(session=cast(AsyncSession, object()))


@pytest.mark.asyncio
async def test_create_package_admin_success() -> None:
    service = _make_service()
    mock_repo = AsyncMock()
    mock_repo.create.return_value = SimpleNamespace(
        id="pkg-1",
        name="Premium",
        description="Full access",
        price=499000,
        duration_days=30,
    )
    service._repo = mock_repo

    payload = PackageCreate(
        name=" Premium ",
        description=" Full access ",
        price=499000,
        duration=30,
    )

    result = await service.create(
        current_user=_make_user(UserRole.ADMIN), payload=payload
    )

    assert result.id == "pkg-1"
    assert result.name == "Premium"
    assert result.description == "Full access"
    assert result.price == 499000
    assert result.duration == 30

    mock_repo.create.assert_awaited_once_with(
        name="Premium",
        description="Full access",
        price=499000,
        duration_days=30,
    )


@pytest.mark.asyncio
async def test_create_package_staff_forbidden() -> None:
    service = _make_service()
    mock_repo = AsyncMock()
    service._repo = mock_repo

    payload = PackageCreate(
        name="Standard",
        description="Basic access",
        price=199000,
        duration=30,
    )

    with pytest.raises(
        ForbiddenException, match="Only admin users can create packages"
    ):
        await service.create(current_user=_make_user(UserRole.STAFF), payload=payload)

    mock_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_list_normalizes_name_filter_and_maps_items() -> None:
    service = _make_service()
    mock_repo = AsyncMock()
    mock_repo.paginate.return_value = PaginatedResponse(
        items=[
            SimpleNamespace(
                id="pkg-1",
                name="Premium",
                description="Full access",
                price=499000,
                duration_days=30,
            )
        ],
        total=1,
        page=1,
        limit=10,
    )
    service._repo = mock_repo

    result = await service.get_list(name="  pre  ", limit=10, page=1)

    assert result.total == 1
    assert result.page == 1
    assert result.limit == 10
    assert len(result.items) == 1
    assert result.items[0].name == "Premium"
    assert result.items[0].duration == 30

    mock_repo.paginate.assert_awaited_once_with(
        page=1,
        limit=10,
        name__ilike="pre",
    )


@pytest.mark.asyncio
async def test_get_list_empty_name_sends_none_filter() -> None:
    service = _make_service()
    mock_repo = AsyncMock()
    mock_repo.paginate.return_value = PaginatedResponse(
        items=[],
        total=0,
        page=1,
        limit=10,
    )
    service._repo = mock_repo

    result = await service.get_list(name="   ", limit=10, page=1)

    assert result.items == []
    assert result.total == 0
    mock_repo.paginate.assert_awaited_once_with(page=1, limit=10, name__ilike=None)
