from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import SubscriptionStatus, UserRole
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.subscription import CreateSubscriptionRequest, SubscriptionListQuery
from app.services.subscription import SubscriptionService


def _make_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id="user-1",
        username="tester",
        password_hash="hashed",
        full_name="Test User",
        role=UserRole.STAFF,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _make_service() -> SubscriptionService:
    return SubscriptionService(session=cast(AsyncSession, object()))


@pytest.mark.asyncio
async def test_create_subscription_sets_created_by() -> None:
    service = _make_service()

    service._member_repo = AsyncMock()
    service._package_repo = AsyncMock()
    service._user_repo = AsyncMock()
    service._repo = AsyncMock()

    service._member_repo.get_by_id.return_value = SimpleNamespace(id="member-1")
    service._package_repo.get_by_id.return_value = SimpleNamespace(id="package-1")
    service._repo.create.return_value = SimpleNamespace(
        id="sub-1",
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        created_by="user-1",
        sold_by="user-2",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    payload = CreateSubscriptionRequest(
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        sold_by="user-2",
    )

    result = await service.create(current_user=_make_user(), payload=payload)

    assert result.id == "sub-1"
    assert result.created_by == "user-1"
    service._repo.create.assert_awaited_once_with(
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status="pending",
        price=499000.0,
        created_by="user-1",
        sold_by="user-2",
    )


@pytest.mark.asyncio
async def test_create_subscription_member_not_found() -> None:
    service = _make_service()

    service._member_repo = AsyncMock()
    service._package_repo = AsyncMock()
    service._user_repo = AsyncMock()
    service._repo = AsyncMock()

    service._member_repo.get_by_id.return_value = None

    payload = CreateSubscriptionRequest(
        member_id="missing-member",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        sold_by=None,
    )

    with pytest.raises(
        NotFoundException, match="Member with id 'missing-member' not found"
    ):
        await service.create(current_user=_make_user(), payload=payload)


@pytest.mark.asyncio
async def test_create_subscription_package_not_found() -> None:
    service = _make_service()

    service._member_repo = AsyncMock()
    service._package_repo = AsyncMock()
    service._user_repo = AsyncMock()
    service._repo = AsyncMock()

    service._member_repo.get_by_id.return_value = SimpleNamespace(id="member-1")
    service._package_repo.get_by_id.return_value = None

    payload = CreateSubscriptionRequest(
        member_id="member-1",
        package_id="missing-package",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        sold_by=None,
    )

    with pytest.raises(
        NotFoundException, match="Package with id 'missing-package' not found"
    ):
        await service.create(current_user=_make_user(), payload=payload)


@pytest.mark.asyncio
async def test_create_subscription_sold_by_not_found() -> None:
    service = _make_service()

    service._member_repo = AsyncMock()
    service._package_repo = AsyncMock()
    service._user_repo = AsyncMock()
    service._repo = AsyncMock()

    service._member_repo.get_by_id.return_value = SimpleNamespace(id="member-1")
    service._package_repo.get_by_id.return_value = SimpleNamespace(id="package-1")
    service._user_repo.get_by_id.return_value = None

    payload = CreateSubscriptionRequest(
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        sold_by="missing-user",
    )

    with pytest.raises(
        NotFoundException, match="User with id 'missing-user' not found for sold_by"
    ):
        await service.create(current_user=_make_user(), payload=payload)


@pytest.mark.asyncio
async def test_get_list_with_optional_dates() -> None:
    service = _make_service()
    service._repo = AsyncMock()

    service._repo.paginate.return_value = PaginatedResponse(
        items=[],
        total=0,
        page=1,
        limit=10,
    )

    query = SubscriptionListQuery(page=1, limit=10)
    result = await service.get_list(query)

    assert result.items == []
    service._repo.paginate.assert_awaited_once_with(
        page=1,
        limit=10,
        start_date=None,
        end_date=None,
        member_id=None,
        status=None,
        package_id=None,
    )


@pytest.mark.asyncio
async def test_get_list_with_all_filters() -> None:
    service = _make_service()
    service._repo = AsyncMock()

    service._repo.paginate.return_value = PaginatedResponse(
        items=[],
        total=0,
        page=2,
        limit=5,
    )

    query = SubscriptionListQuery(
        page=2,
        limit=5,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        member_id="member-1",
        status=SubscriptionStatus.ACTIVE,
        package_id="package-1",
    )
    await service.get_list(query)

    service._repo.paginate.assert_awaited_once_with(
        page=2,
        limit=5,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        member_id="member-1",
        status="active",
        package_id="package-1",
    )
