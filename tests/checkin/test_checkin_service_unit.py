from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.schemas.checkin import CreateCheckInRequest
from app.services.checkin import CheckInService


def _make_service() -> CheckInService:
    return CheckInService(session=cast(AsyncSession, object()))


@pytest.mark.asyncio
async def test_create_checkin_success() -> None:
    service = _make_service()

    service._repo = AsyncMock()
    service._member_repo = AsyncMock()
    service._subscription_repo = AsyncMock()

    now = datetime.now(timezone.utc)
    member = SimpleNamespace(id="member-1")
    subscription = SimpleNamespace(id="sub-1", member_id="member-1", status="active")
    checkin = SimpleNamespace(
        id="checkin-1",
        member_id="member-1",
        checked_in_at=now,
        note="First check-in",
        created_at=now,
        updated_at=now,
    )

    service._member_repo.get_by_id.return_value = member
    service._subscription_repo.get_active_subscription.return_value = subscription
    service._repo.create.return_value = checkin

    payload = CreateCheckInRequest(
        member_id="member-1",
        checked_in_at=now,
        note="First check-in",
    )

    result = await service.create(payload)

    assert result.id == "checkin-1"
    assert result.member_id == "member-1"
    assert result.note == "First check-in"
    service._member_repo.get_by_id.assert_awaited_once_with("member-1")
    service._subscription_repo.get_active_subscription.assert_awaited_once_with(
        member_id="member-1", check_date=now.date()
    )
    service._repo.create.assert_awaited_once_with(
        member_id="member-1",
        checked_in_at=now,
        note="First check-in",
    )


@pytest.mark.asyncio
async def test_create_checkin_member_not_found() -> None:
    """Test check-in creation fails when member doesn't exist."""
    service = _make_service()

    service._repo = AsyncMock()
    service._member_repo = AsyncMock()
    service._subscription_repo = AsyncMock()

    service._member_repo.get_by_id.return_value = None

    now = datetime.now(timezone.utc)
    payload = CreateCheckInRequest(
        member_id="missing-member",
        checked_in_at=now,
        note=None,
    )

    with pytest.raises(NotFoundException, match="Member not found"):
        await service.create(payload)

    service._member_repo.get_by_id.assert_awaited_once_with("missing-member")
    service._subscription_repo.get_active_subscription.assert_not_awaited()
    service._repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_checkin_no_active_subscription() -> None:
    """Test check-in creation fails when member has no active subscription."""
    service = _make_service()

    service._repo = AsyncMock()
    service._member_repo = AsyncMock()
    service._subscription_repo = AsyncMock()

    member = SimpleNamespace(id="member-1")
    service._member_repo.get_by_id.return_value = member
    service._subscription_repo.get_active_subscription.return_value = None

    now = datetime.now(timezone.utc)
    check_date = now.date()
    payload = CreateCheckInRequest(
        member_id="member-1",
        checked_in_at=now,
        note=None,
    )

    with pytest.raises(
        NotFoundException,
        match="Member has no active subscription on the given date",
    ):
        await service.create(payload)

    service._member_repo.get_by_id.assert_awaited_once_with("member-1")
    service._subscription_repo.get_active_subscription.assert_awaited_once_with(
        member_id="member-1", check_date=check_date
    )
    service._repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_history_success_with_date_range() -> None:
    """Test retrieving check-in history with date filtering."""
    service = _make_service()

    service._repo = AsyncMock()

    now = datetime.now(timezone.utc)
    checkins = [
        SimpleNamespace(
            id="checkin-1",
            member_id="member-1",
            checked_in_at=now,
            note="Morning session",
            created_at=now,
            updated_at=now,
        ),
        SimpleNamespace(
            id="checkin-2",
            member_id="member-1",
            checked_in_at=datetime(2026, 6, 28, 18, 0, 0, tzinfo=timezone.utc),
            note="Evening session",
            created_at=datetime(2026, 6, 28, 18, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 28, 18, 0, 0, tzinfo=timezone.utc),
        ),
    ]

    service._repo.get_history.return_value = (checkins, 2)

    result, total = await service.get_history(
        member_id="member-1",
        from_date="2026-06-28",
        to_date="2026-06-29",
        page=1,
        limit=20,
    )

    assert len(result) == 2
    assert total == 2
    assert result[0].id == "checkin-1"
    assert result[1].id == "checkin-2"
    service._repo.get_history.assert_awaited_once_with(
        member_id="member-1",
        from_date=date(2026, 6, 28),
        to_date=date(2026, 6, 29),
        skip=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_get_history_success_without_date_range() -> None:
    """Test retrieving check-in history without date filtering."""
    service = _make_service()

    service._repo = AsyncMock()

    now = datetime.now(timezone.utc)
    checkins = [
        SimpleNamespace(
            id="checkin-1",
            member_id="member-1",
            checked_in_at=now,
            note="Check-in",
            created_at=now,
            updated_at=now,
        ),
    ]

    service._repo.get_history.return_value = (checkins, 1)

    result, total = await service.get_history(
        member_id="member-1",
        from_date=None,
        to_date=None,
        page=1,
        limit=20,
    )

    assert len(result) == 1
    assert total == 1
    service._repo.get_history.assert_awaited_once_with(
        member_id="member-1",
        from_date=None,
        to_date=None,
        skip=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_get_history_with_pagination() -> None:
    """Test pagination of check-in history."""
    service = _make_service()

    service._repo = AsyncMock()

    now = datetime.now(timezone.utc)
    checkins = [
        SimpleNamespace(
            id="checkin-3",
            member_id="member-1",
            checked_in_at=now,
            note="Page 2",
            created_at=now,
            updated_at=now,
        ),
    ]

    service._repo.get_history.return_value = (checkins, 25)

    result, total = await service.get_history(
        member_id="member-1",
        page=2,
        limit=20,
    )

    assert len(result) == 1
    assert total == 25
    service._repo.get_history.assert_awaited_once_with(
        member_id="member-1",
        from_date=None,
        to_date=None,
        skip=20,  # (page 2 - 1) * limit 20
        limit=20,
    )


@pytest.mark.asyncio
async def test_get_history_invalid_from_date_format() -> None:
    """Test history retrieval fails with invalid from_date format."""
    service = _make_service()

    service._repo = AsyncMock()

    with pytest.raises(ValidationException, match="Invalid from_date format"):
        await service.get_history(
            member_id="member-1",
            from_date="28-06-2026",  # Invalid format
            page=1,
            limit=20,
        )

    service._repo.get_history.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_history_invalid_to_date_format() -> None:
    """Test history retrieval fails with invalid to_date format."""
    service = _make_service()

    service._repo = AsyncMock()

    with pytest.raises(ValidationException, match="Invalid to_date format"):
        await service.get_history(
            member_id="member-1",
            from_date="2026-06-28",
            to_date="29/06/2026",  # Invalid format
            page=1,
            limit=20,
        )

    service._repo.get_history.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_history_empty_result() -> None:
    """Test retrieving check-in history when no records exist."""
    service = _make_service()

    service._repo = AsyncMock()

    service._repo.get_history.return_value = ([], 0)

    result, total = await service.get_history(
        member_id="member-1",
        page=1,
        limit=20,
    )

    assert len(result) == 0
    assert total == 0
    service._repo.get_history.assert_awaited_once()
