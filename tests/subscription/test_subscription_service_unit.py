from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import SubscriptionStatus, UserRole
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.subscription import (
    CreateSubscriptionRequest,
    SubscriptionListQuery,
    UpdateSubscriptionRequest,
)
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


def _make_package(
    package_id: str = "package-1",
    duration_days: int = 30,
) -> SimpleNamespace:
    return SimpleNamespace(id=package_id, duration_days=duration_days)


@pytest.mark.asyncio
async def test_create_subscription_sets_created_by_and_pending_status() -> None:
    service = _make_service()

    service._member_repo = AsyncMock()
    service._package_repo = AsyncMock()
    service._repo = AsyncMock()

    service._member_repo.get_by_id.return_value = SimpleNamespace(id="member-1")
    service._package_repo.get_by_id.return_value = _make_package(duration_days=30)
    service._repo.get_overlapping_for_member.return_value = None
    service._repo.create.return_value = SimpleNamespace(
        id="sub-1",
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        created_by="user-1",
        updated_by=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    payload = CreateSubscriptionRequest(
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        price=499000.0,
    )

    result = await service.create(current_user=_make_user(), payload=payload)

    assert result.id == "sub-1"
    assert result.created_by == "user-1"
    assert result.updated_by is None
    assert result.status == SubscriptionStatus.PENDING
    service._repo.get_overlapping_for_member.assert_awaited_once_with(
        member_id="member-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        exclude_subscription_id=None,
    )
    service._repo.create.assert_awaited_once_with(
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        created_by="user-1",
    )


@pytest.mark.asyncio
async def test_create_subscription_conflicts_on_overlapping_period() -> None:
    service = _make_service()

    service._member_repo = AsyncMock()
    service._package_repo = AsyncMock()
    service._repo = AsyncMock()

    service._member_repo.get_by_id.return_value = SimpleNamespace(id="member-1")
    service._package_repo.get_by_id.return_value = _make_package(duration_days=30)
    service._repo.get_overlapping_for_member.return_value = SimpleNamespace(
        id="sub-existing",
        status=SubscriptionStatus.ACTIVE,
    )

    payload = CreateSubscriptionRequest(
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        price=499000.0,
    )

    with pytest.raises(
        BadRequestException,
        match="Member with id 'member-1' already has a subscription covering the selected period",
    ):
        await service.create(current_user=_make_user(), payload=payload)

    service._repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_subscription_recalculates_end_date_and_sets_updated_by() -> None:
    service = _make_service()

    service._package_repo = AsyncMock()
    service._repo = AsyncMock()
    current_user = _make_user()

    current_subscription = SimpleNamespace(
        id="sub-1",
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        created_by="user-1",
        updated_by=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    updated_subscription = SimpleNamespace(
        **{
            **current_subscription.__dict__,
            "package_id": "package-2",
            "start_date": date(2026, 6, 10),
            "end_date": date(2026, 8, 9),
            "price": 599000.0,
            "updated_by": current_user.id,
        }
    )

    service._repo.get_by_id.return_value = current_subscription
    service._package_repo.get_by_id.return_value = _make_package(
        package_id="package-2",
        duration_days=60,
    )
    service._repo.get_overlapping_for_member.return_value = None
    service._repo.update.return_value = updated_subscription

    payload = UpdateSubscriptionRequest(
        package_id="package-2",
        start_date=date(2026, 6, 10),
        price=599000.0,
    )

    result = await service.update(
        subscription_id="sub-1",
        current_user=current_user,
        payload=payload,
    )

    assert result.end_date == date(2026, 8, 9)
    assert result.updated_by == current_user.id
    service._repo.update.assert_awaited_once_with(
        current_subscription,
        package_id="package-2",
        start_date=date(2026, 6, 10),
        price=599000.0,
        end_date=date(2026, 8, 9),
        updated_by="user-1",
    )
    service._repo.get_overlapping_for_member.assert_awaited_once_with(
        member_id="member-1",
        start_date=date(2026, 6, 10),
        end_date=date(2026, 8, 9),
        exclude_subscription_id="sub-1",
    )


@pytest.mark.asyncio
async def test_update_subscription_conflicts_on_overlapping_period() -> None:
    service = _make_service()

    service._package_repo = AsyncMock()
    service._repo = AsyncMock()
    current_user = _make_user()

    current_subscription = SimpleNamespace(
        id="sub-1",
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        created_by="user-1",
        updated_by=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    service._repo.get_by_id.return_value = current_subscription
    service._package_repo.get_by_id.return_value = _make_package(duration_days=30)
    service._repo.get_overlapping_for_member.return_value = SimpleNamespace(
        id="sub-existing",
        status=SubscriptionStatus.ACTIVE,
    )

    payload = UpdateSubscriptionRequest(
        start_date=date(2026, 6, 10),
        price=599000.0,
    )

    with pytest.raises(
        BadRequestException,
        match="Member with id 'member-1' already has a subscription covering the selected period",
    ):
        await service.update(
            subscription_id="sub-1",
            current_user=current_user,
            payload=payload,
        )

    service._repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_activate_subscription_success() -> None:
    service = _make_service()
    service._repo = AsyncMock()

    subscription = SimpleNamespace(
        id="sub-1",
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.PENDING,
        price=499000.0,
        created_by="user-1",
        updated_by=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    activated_subscription = SimpleNamespace(
        **{
            **subscription.__dict__,
            "status": SubscriptionStatus.ACTIVE,
            "updated_by": "user-1",
        }
    )

    service._repo.get_by_id.return_value = subscription
    service._repo.get_overlapping_for_member.return_value = None
    service._repo.update.return_value = activated_subscription

    result = await service.activate(subscription_id="sub-1", current_user=_make_user())

    assert result.status == SubscriptionStatus.ACTIVE
    assert result.updated_by == "user-1"
    service._repo.get_overlapping_for_member.assert_awaited_once_with(
        member_id="member-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        exclude_subscription_id="sub-1",
    )
    service._repo.update.assert_awaited_once_with(
        subscription,
        status=SubscriptionStatus.ACTIVE,
        updated_by="user-1",
    )


@pytest.mark.asyncio
async def test_activate_subscription_already_active() -> None:
    service = _make_service()
    service._repo = AsyncMock()

    subscription = SimpleNamespace(
        id="sub-1",
        status=SubscriptionStatus.ACTIVE,
    )
    service._repo.get_by_id.return_value = subscription

    with pytest.raises(
        BadRequestException,
        match="Subscription with id 'sub-1' is already active",
    ):
        await service.activate(subscription_id="sub-1", current_user=_make_user())

    service._repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_subscription_success() -> None:
    service = _make_service()
    service._repo = AsyncMock()

    subscription = SimpleNamespace(
        id="sub-1",
        member_id="member-1",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
        status=SubscriptionStatus.ACTIVE,
        price=499000.0,
        created_by="user-1",
        updated_by=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    cancelled_subscription = SimpleNamespace(
        **{
            **subscription.__dict__,
            "status": SubscriptionStatus.CANCELLED,
            "updated_by": "user-1",
        }
    )

    service._repo.get_by_id.return_value = subscription
    service._repo.update.return_value = cancelled_subscription

    result = await service.cancel(subscription_id="sub-1", current_user=_make_user())

    assert result.status == SubscriptionStatus.CANCELLED
    assert result.updated_by == "user-1"
    service._repo.update.assert_awaited_once_with(
        subscription,
        status=SubscriptionStatus.CANCELLED,
        updated_by="user-1",
    )


@pytest.mark.asyncio
async def test_cancel_subscription_not_found() -> None:
    service = _make_service()
    service._repo = AsyncMock()
    service._repo.get_by_id.return_value = None

    with pytest.raises(
        NotFoundException,
        match="Subscription with id 'sub-missing' not found",
    ):
        await service.cancel(subscription_id="sub-missing", current_user=_make_user())


@pytest.mark.asyncio
async def test_cancel_subscription_already_cancelled() -> None:
    service = _make_service()
    service._repo = AsyncMock()

    subscription = SimpleNamespace(
        id="sub-1",
        status=SubscriptionStatus.CANCELLED,
    )
    service._repo.get_by_id.return_value = subscription

    with pytest.raises(
        BadRequestException,
        match="Subscription with id 'sub-1' is already cancelled",
    ):
        await service.cancel(subscription_id="sub-1", current_user=_make_user())

    service._repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_subscription_member_not_found() -> None:
    service = _make_service()

    service._member_repo = AsyncMock()
    service._package_repo = AsyncMock()
    service._repo = AsyncMock()

    service._member_repo.get_by_id.return_value = None

    payload = CreateSubscriptionRequest(
        member_id="missing-member",
        package_id="package-1",
        start_date=date(2026, 6, 1),
        price=499000.0,
    )

    with pytest.raises(
        NotFoundException,
        match="Member with id 'missing-member' not found",
    ):
        await service.create(current_user=_make_user(), payload=payload)


@pytest.mark.asyncio
async def test_create_subscription_package_not_found() -> None:
    service = _make_service()

    service._member_repo = AsyncMock()
    service._package_repo = AsyncMock()
    service._repo = AsyncMock()

    service._member_repo.get_by_id.return_value = SimpleNamespace(id="member-1")
    service._package_repo.get_by_id.return_value = None

    payload = CreateSubscriptionRequest(
        member_id="member-1",
        package_id="missing-package",
        start_date=date(2026, 6, 1),
        price=499000.0,
    )

    with pytest.raises(
        NotFoundException,
        match="Package with id 'missing-package' not found",
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
        start_date__gte=None,
        end_date__lte=None,
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
        start_date__gte=date(2026, 6, 1),
        end_date__lte=date(2026, 7, 1),
        member_id="member-1",
        status="active",
        package_id="package-1",
    )
