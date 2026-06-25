"""Unit tests for MemberService."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import cast
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException
from app.models.member import Member
from app.schemas.member import CreateMemberRequest
from app.services.member import MemberService


def _make_member(
    phone: str = "0901234567",
    full_name: str = "Test Member",
    date_of_birth: date | None = None,
    gender: str | None = None,
) -> Member:
    """Create a test member."""
    now = datetime.now(timezone.utc)
    return Member(
        id="member-1",
        phone=phone,
        full_name=full_name,
        date_of_birth=date_of_birth,
        gender=gender,
        avatar_url=None,
        note=None,
        created_at=now,
        updated_at=now,
    )


def _make_member_service() -> MemberService:
    """Create a MemberService with mock session."""
    return MemberService(session=cast(AsyncSession, object()))


@pytest.mark.asyncio
async def test_create_member_success_with_valid_data() -> None:
    """Test create_member returns created member with valid data."""
    service = _make_member_service()
    mock_repo = AsyncMock()

    new_member = _make_member(
        phone="0901234567", full_name="John Doe", date_of_birth=date(1990, 1, 1)
    )
    mock_repo.get_one.return_value = None  # Phone doesn't exist
    mock_repo.create.return_value = new_member
    service._repo = mock_repo

    request_data = CreateMemberRequest(
        phone="0901234567",
        full_name="John Doe",
        date_of_birth=date(1990, 1, 1),
    )

    result = await service.create(request_data)

    assert result.phone == "0901234567"
    assert result.full_name == "John Doe"
    assert result.date_of_birth == date(1990, 1, 1)
    mock_repo.get_one.assert_awaited_once_with({"phone": "0901234567"})
    mock_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_member_fails_with_duplicate_phone() -> None:
    """Test create_member raises ConflictException for duplicate phone."""
    service = _make_member_service()
    mock_repo = AsyncMock()

    # Phone already exists
    existing_member = _make_member(phone="0901234567")
    mock_repo.get_one.return_value = existing_member
    service._repo = mock_repo

    request_data = CreateMemberRequest(
        phone="0901234567",
        full_name="John Doe",
    )

    with pytest.raises(ConflictException) as exc_info:
        await service.create(request_data)

    assert "already exists" in str(exc_info.value)
    mock_repo.get_one.assert_awaited_once_with({"phone": "0901234567"})


@pytest.mark.asyncio
async def test_create_member_preserves_phone() -> None:
    """Test create_member preserves phone from request."""
    service = _make_member_service()
    mock_repo = AsyncMock()

    new_member = _make_member(phone="+84901234567")
    mock_repo.get_one.return_value = None
    mock_repo.create.return_value = new_member
    service._repo = mock_repo

    request_data = CreateMemberRequest(
        phone="+84901234567",
        full_name="Member",
    )

    result = await service.create(request_data)

    assert result.phone == "+84901234567"


@pytest.mark.asyncio
async def test_create_member_preserves_full_name() -> None:
    """Test create_member preserves full_name from request."""
    service = _make_member_service()
    mock_repo = AsyncMock()

    new_member = _make_member(full_name="José García-López")
    mock_repo.get_one.return_value = None
    mock_repo.create.return_value = new_member
    service._repo = mock_repo

    request_data = CreateMemberRequest(
        phone="0901234567",
        full_name="José García-López",
    )

    result = await service.create(request_data)

    assert result.full_name == "José García-López"


@pytest.mark.asyncio
async def test_get_list_returns_paginated_members() -> None:
    """Test get_list returns paginated members."""
    from app.schemas.common import PaginatedResponse
    from app.schemas.member import MemberListQuery

    service = _make_member_service()
    mock_repo = AsyncMock()

    members = [
        _make_member(phone="0901111111", full_name="Member 1"),
        _make_member(phone="0902222222", full_name="Member 2"),
    ]

    paginated = PaginatedResponse(
        items=members,
        total=2,
        page=1,
        limit=10,
    )
    mock_repo.paginate.return_value = paginated
    service._repo = mock_repo

    query = MemberListQuery(page=1, limit=10)
    result = await service.get_list(query)

    assert len(result.items) == 2
    assert result.total == 2
    assert result.page == 1
    mock_repo.paginate.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_list_with_phone_filter() -> None:
    """Test get_list filters by phone."""
    from app.schemas.common import PaginatedResponse
    from app.schemas.member import MemberListQuery

    service = _make_member_service()
    mock_repo = AsyncMock()

    member = _make_member(phone="0901234567")

    paginated = PaginatedResponse(
        items=[member],
        total=1,
        page=1,
        limit=10,
    )
    mock_repo.paginate.return_value = paginated
    service._repo = mock_repo

    query = MemberListQuery(phone="0901234567", page=1, limit=10)
    result = await service.get_list(query)

    assert len(result.items) == 1
    mock_repo.paginate.assert_awaited_once_with(
        page=1, limit=10, phone__ilike="0901234567"
    )


@pytest.mark.asyncio
async def test_get_list_with_full_name_filter() -> None:
    """Test get_list filters by full_name."""
    from app.schemas.common import PaginatedResponse
    from app.schemas.member import MemberListQuery

    service = _make_member_service()
    mock_repo = AsyncMock()

    member = _make_member(full_name="John")

    paginated = PaginatedResponse(
        items=[member],
        total=1,
        page=1,
        limit=10,
    )
    mock_repo.paginate.return_value = paginated
    service._repo = mock_repo

    query = MemberListQuery(full_name="John", page=1, limit=10)
    result = await service.get_list(query)

    assert len(result.items) == 1
    mock_repo.paginate.assert_awaited_once_with(
        page=1, limit=10, full_name__ilike="John"
    )


@pytest.mark.asyncio
async def test_get_list_with_pagination() -> None:
    """Test get_list respects pagination parameters."""
    from app.schemas.common import PaginatedResponse
    from app.schemas.member import MemberListQuery

    service = _make_member_service()
    mock_repo = AsyncMock()

    paginated = PaginatedResponse(items=[], total=0, page=2, limit=5)
    mock_repo.paginate.return_value = paginated
    service._repo = mock_repo

    query = MemberListQuery(page=2, limit=5)
    result = await service.get_list(query)

    assert result.page == 2
    assert result.limit == 5
    mock_repo.paginate.assert_awaited_once_with(page=2, limit=5)


@pytest.mark.asyncio
async def test_get_member_success() -> None:
    """Test get returns member when found."""
    service = _make_member_service()
    mock_repo = AsyncMock()

    member = _make_member(phone="0901234567", full_name="John Doe")
    mock_repo.get_by_id.return_value = member
    service._repo = mock_repo

    result = await service.get("member-1")

    assert result.id == "member-1"
    assert result.phone == "0901234567"
    assert result.full_name == "John Doe"
    mock_repo.get_by_id.assert_awaited_once_with("member-1")


@pytest.mark.asyncio
async def test_get_member_not_found() -> None:
    """Test get raises NotFoundException when member not found."""
    from app.core.exceptions import NotFoundException

    service = _make_member_service()
    mock_repo = AsyncMock()

    mock_repo.get_by_id.return_value = None
    service._repo = mock_repo

    with pytest.raises(NotFoundException) as exc_info:
        await service.get("invalid-id")

    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_member_success() -> None:
    """Test update updates member with new data."""
    from app.schemas.member import UpdateMemberRequest

    service = _make_member_service()
    mock_repo = AsyncMock()

    existing_member = _make_member(phone="0901234567", full_name="John Doe")
    updated_member = _make_member(
        phone="0909999999", full_name="Jane Doe", gender="Female"
    )

    mock_repo.get_by_id.return_value = existing_member
    mock_repo.get_one.return_value = None  # No existing member with new phone
    mock_repo.update.return_value = updated_member
    service._repo = mock_repo

    request_data = UpdateMemberRequest(
        phone="0909999999",
        full_name="Jane Doe",
        gender="Female",
    )

    result = await service.update("member-1", request_data)

    assert result.phone == "0909999999"
    assert result.full_name == "Jane Doe"
    assert result.gender == "Female"
    mock_repo.get_by_id.assert_awaited_once_with("member-1")
    mock_repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_member_not_found() -> None:
    """Test update raises NotFoundException when member not found."""
    from app.core.exceptions import NotFoundException
    from app.schemas.member import UpdateMemberRequest

    service = _make_member_service()
    mock_repo = AsyncMock()

    mock_repo.get_by_id.return_value = None
    service._repo = mock_repo

    request_data = UpdateMemberRequest(full_name="New Name")

    with pytest.raises(NotFoundException) as exc_info:
        await service.update("invalid-id", request_data)

    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_member_duplicate_phone() -> None:
    """Test update raises ConflictException when phone already exists."""
    from app.schemas.member import UpdateMemberRequest

    service = _make_member_service()
    mock_repo = AsyncMock()

    existing_member = _make_member(phone="0901234567")
    other_member = _make_member(phone="0909999999")  # Phone being changed to

    mock_repo.get_by_id.return_value = existing_member
    mock_repo.get_one.return_value = other_member  # Phone already exists
    service._repo = mock_repo

    request_data = UpdateMemberRequest(phone="0909999999")

    with pytest.raises(ConflictException) as exc_info:
        await service.update("member-1", request_data)

    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_member_partial() -> None:
    """Test update with only some fields changed."""
    from app.schemas.member import UpdateMemberRequest

    service = _make_member_service()
    mock_repo = AsyncMock()

    existing_member = _make_member(phone="0901234567", full_name="John Doe")
    updated_member = _make_member(
        phone="0901234567",
        full_name="Updated Name",  # Only name changed
    )

    mock_repo.get_by_id.return_value = existing_member
    mock_repo.update.return_value = updated_member
    service._repo = mock_repo

    request_data = UpdateMemberRequest(full_name="Updated Name")  # Only this field

    result = await service.update("member-1", request_data)

    assert result.full_name == "Updated Name"
    assert result.phone == "0901234567"  # Unchanged
    mock_repo.update.assert_awaited_once()

    # Verify only updated field was passed
    call_kwargs = mock_repo.update.call_args[1]
    assert "full_name" in call_kwargs
    assert call_kwargs["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_member_success() -> None:
    """Test delete removes member when found."""
    service = _make_member_service()
    mock_repo = AsyncMock()

    member = _make_member(phone="0901234567")
    mock_repo.get_by_id.return_value = member
    mock_repo.delete.return_value = None
    service._repo = mock_repo

    await service.delete("member-1")

    mock_repo.get_by_id.assert_awaited_once_with("member-1")
    mock_repo.delete.assert_awaited_once_with(member)


@pytest.mark.asyncio
async def test_delete_member_not_found() -> None:
    """Test delete raises NotFoundException when member not found."""
    from app.core.exceptions import NotFoundException

    service = _make_member_service()
    mock_repo = AsyncMock()

    mock_repo.get_by_id.return_value = None
    service._repo = mock_repo

    with pytest.raises(NotFoundException) as exc_info:
        await service.delete("invalid-id")

    assert "not found" in str(exc_info.value)
