"""Unit tests for MemberSubscriptionService."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.member import Member
from app.models.member_subscription import MemberSubscription
from app.models.package import Package
from app.schemas.member_subscription import CreateMemberSubscriptionRequest
from app.services.member_subscription import MemberSubscriptionService


def _make_member(
    member_id: str = "member-1",
    phone: str = "0901234567",
    full_name: str = "Test Member",
) -> Member:
    """Create a test member."""
    now = datetime.now(timezone.utc)
    return Member(
        id=member_id,
        phone=phone,
        full_name=full_name,
        date_of_birth=None,
        gender=None,
        avatar_url=None,
        note=None,
        created_at=now,
        updated_at=now,
    )


def _make_package(
    package_id: str = "package-1",
    name: str = "Standard",
    duration_days: int = 30,
    price: Decimal = Decimal("99.99"),
    is_active: bool = True,
) -> Package:
    """Create a test package."""
    now = datetime.now(timezone.utc)
    return Package(
        id=package_id,
        name=name,
        description="Test package",
        duration_days=duration_days,
        price=price,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


def _make_subscription(
    subscription_id: str = "sub-1",
    member_id: str = "member-1",
    package_id: str = "package-1",
    is_active: bool = True,
) -> MemberSubscription:
    """Create a test subscription."""
    now = datetime.now(timezone.utc)
    start_date = now
    end_date = now + timedelta(days=30)
    return MemberSubscription(
        id=subscription_id,
        member_id=member_id,
        package_id=package_id,
        subscription_start_date=start_date,
        subscription_end_date=end_date,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


def _make_service() -> MemberSubscriptionService:
    """Create a MemberSubscriptionService with mock session."""
    return MemberSubscriptionService(session=cast(AsyncSession, object()))


@pytest.mark.asyncio
async def test_create_subscription_success_with_valid_data() -> None:
    """Test create subscription returns created subscription with valid data."""
    service = _make_service()
    mock_member_repo = AsyncMock()
    mock_package_repo = AsyncMock()
    mock_subscription_repo = AsyncMock()

    member = _make_member()
    package = _make_package()
    subscription = _make_subscription()

    mock_member_repo.get_by_id.return_value = member
    mock_package_repo.get_by_id.return_value = package
    mock_subscription_repo.get_one.return_value = None  # No existing subscription
    mock_subscription_repo.create.return_value = subscription

    service._member_repo = mock_member_repo
    service._package_repo = mock_package_repo
    service._subscription_repo = mock_subscription_repo

    request_data = CreateMemberSubscriptionRequest(package_id="package-1")

    result = await service.create("member-1", request_data)

    assert result.member_id == "member-1"
    assert result.package_id == "package-1"
    assert result.is_active is True
    mock_member_repo.get_by_id.assert_awaited_once_with("member-1")
    mock_package_repo.get_by_id.assert_awaited_once_with("package-1")
    mock_subscription_repo.get_one.assert_awaited_once_with(
        {"member_id": "member-1", "is_active": True}
    )
    mock_subscription_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_subscription_fails_member_not_found() -> None:
    """Test create subscription raises NotFoundException when member not found."""
    service = _make_service()
    mock_member_repo = AsyncMock()
    mock_package_repo = AsyncMock()
    mock_subscription_repo = AsyncMock()

    mock_member_repo.get_by_id.return_value = None  # Member not found
    service._member_repo = mock_member_repo
    service._package_repo = mock_package_repo
    service._subscription_repo = mock_subscription_repo

    request_data = CreateMemberSubscriptionRequest(package_id="package-1")

    with pytest.raises(NotFoundException) as exc_info:
        await service.create("member-not-exist", request_data)

    assert "Member with id 'member-not-exist' not found" in str(exc_info.value)
    mock_member_repo.get_by_id.assert_awaited_once_with("member-not-exist")


@pytest.mark.asyncio
async def test_create_subscription_fails_package_not_found() -> None:
    """Test create subscription raises NotFoundException when package not found."""
    service = _make_service()
    mock_member_repo = AsyncMock()
    mock_package_repo = AsyncMock()
    mock_subscription_repo = AsyncMock()

    member = _make_member()
    mock_member_repo.get_by_id.return_value = member
    mock_package_repo.get_by_id.return_value = None  # Package not found
    service._member_repo = mock_member_repo
    service._package_repo = mock_package_repo
    service._subscription_repo = mock_subscription_repo

    request_data = CreateMemberSubscriptionRequest(package_id="package-not-exist")

    with pytest.raises(NotFoundException) as exc_info:
        await service.create("member-1", request_data)

    assert "Package with id 'package-not-exist' not found" in str(exc_info.value)
    mock_member_repo.get_by_id.assert_awaited_once_with("member-1")
    mock_package_repo.get_by_id.assert_awaited_once_with("package-not-exist")


@pytest.mark.asyncio
async def test_create_subscription_fails_package_not_active() -> None:
    """Test create subscription raises ConflictException when package not active."""
    service = _make_service()
    mock_member_repo = AsyncMock()
    mock_package_repo = AsyncMock()
    mock_subscription_repo = AsyncMock()

    member = _make_member()
    inactive_package = _make_package(is_active=False)

    mock_member_repo.get_by_id.return_value = member
    mock_package_repo.get_by_id.return_value = inactive_package
    service._member_repo = mock_member_repo
    service._package_repo = mock_package_repo
    service._subscription_repo = mock_subscription_repo

    request_data = CreateMemberSubscriptionRequest(package_id="package-1")

    with pytest.raises(ConflictException) as exc_info:
        await service.create("member-1", request_data)

    assert "Package with id 'package-1' is not active" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_subscription_fails_already_has_active() -> None:
    """Test create subscription raises ConflictException when member already has active subscription."""
    service = _make_service()
    mock_member_repo = AsyncMock()
    mock_package_repo = AsyncMock()
    mock_subscription_repo = AsyncMock()

    member = _make_member()
    package = _make_package()
    existing_subscription = _make_subscription()

    mock_member_repo.get_by_id.return_value = member
    mock_package_repo.get_by_id.return_value = package
    mock_subscription_repo.get_one.return_value = existing_subscription
    service._member_repo = mock_member_repo
    service._package_repo = mock_package_repo
    service._subscription_repo = mock_subscription_repo

    request_data = CreateMemberSubscriptionRequest(package_id="package-1")

    with pytest.raises(ConflictException) as exc_info:
        await service.create("member-1", request_data)

    assert "Member 'member-1' already has an active subscription" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_subscription_calculates_end_date_correctly() -> None:
    """Test create subscription calculates end_date correctly based on package duration."""
    service = _make_service()
    mock_member_repo = AsyncMock()
    mock_package_repo = AsyncMock()
    mock_subscription_repo = AsyncMock()

    member = _make_member()
    package_60_days = _make_package(duration_days=60)
    subscription = _make_subscription()

    mock_member_repo.get_by_id.return_value = member
    mock_package_repo.get_by_id.return_value = package_60_days
    mock_subscription_repo.get_one.return_value = None
    mock_subscription_repo.create.return_value = subscription

    service._member_repo = mock_member_repo
    service._package_repo = mock_package_repo
    service._subscription_repo = mock_subscription_repo

    request_data = CreateMemberSubscriptionRequest(package_id="package-1")

    await service.create("member-1", request_data)

    # Verify create was called with correct arguments
    call_kwargs = mock_subscription_repo.create.call_args[1]
    assert call_kwargs["member_id"] == "member-1"
    assert call_kwargs["package_id"] == "package-1"
    assert call_kwargs["is_active"] is True
    # End date should be start date + 60 days
    assert call_kwargs["subscription_end_date"] == call_kwargs[
        "subscription_start_date"
    ] + timedelta(days=60)


@pytest.mark.asyncio
async def test_create_subscription_preserves_package_id() -> None:
    """Test create subscription preserves package_id from request."""
    service = _make_service()
    mock_member_repo = AsyncMock()
    mock_package_repo = AsyncMock()
    mock_subscription_repo = AsyncMock()

    member = _make_member()
    package = _make_package(package_id="special-package")
    subscription = _make_subscription(package_id="special-package")

    mock_member_repo.get_by_id.return_value = member
    mock_package_repo.get_by_id.return_value = package
    mock_subscription_repo.get_one.return_value = None
    mock_subscription_repo.create.return_value = subscription

    service._member_repo = mock_member_repo
    service._package_repo = mock_package_repo
    service._subscription_repo = mock_subscription_repo

    request_data = CreateMemberSubscriptionRequest(package_id="special-package")

    result = await service.create("member-1", request_data)

    assert result.package_id == "special-package"


@pytest.mark.asyncio
async def test_create_subscription_has_timezone_aware_dates() -> None:
    """Test create subscription uses timezone-aware datetime for start and end dates."""
    service = _make_service()
    mock_member_repo = AsyncMock()
    mock_package_repo = AsyncMock()
    mock_subscription_repo = AsyncMock()

    member = _make_member()
    package = _make_package()
    subscription = _make_subscription()

    mock_member_repo.get_by_id.return_value = member
    mock_package_repo.get_by_id.return_value = package
    mock_subscription_repo.get_one.return_value = None
    mock_subscription_repo.create.return_value = subscription

    service._member_repo = mock_member_repo
    service._package_repo = mock_package_repo
    service._subscription_repo = mock_subscription_repo

    request_data = CreateMemberSubscriptionRequest(package_id="package-1")

    await service.create("member-1", request_data)

    # Verify create was called with timezone-aware datetimes
    call_kwargs = mock_subscription_repo.create.call_args[1]
    assert call_kwargs["subscription_start_date"].tzinfo is not None
    assert call_kwargs["subscription_end_date"].tzinfo is not None


@pytest.mark.asyncio
async def test_create_subscription_handles_integrity_error_on_concurrent_request() -> (
    None
):
    """Test create subscription handles IntegrityError (concurrent request race)."""
    from sqlalchemy import exc

    service = _make_service()
    mock_member_repo = AsyncMock()
    mock_package_repo = AsyncMock()
    mock_subscription_repo = AsyncMock()
    mock_session = AsyncMock()

    member = _make_member()
    package = _make_package()

    mock_member_repo.get_by_id.return_value = member
    mock_package_repo.get_by_id.return_value = package
    mock_subscription_repo.get_one.return_value = None
    # Simulate concurrent request creating subscription (IntegrityError)
    mock_subscription_repo.create.side_effect = exc.IntegrityError(
        statement="INSERT", params={}, orig=Exception("unique constraint")
    )
    mock_subscription_repo.session = mock_session

    service._member_repo = mock_member_repo
    service._package_repo = mock_package_repo
    service._subscription_repo = mock_subscription_repo

    request_data = CreateMemberSubscriptionRequest(package_id="package-1")

    with pytest.raises(ConflictException) as exc_info:
        await service.create("member-1", request_data)

    assert "Member 'member-1' already has an active subscription" in str(exc_info.value)
    mock_session.rollback.assert_awaited_once()
