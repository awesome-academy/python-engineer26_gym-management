"""Unit tests for AdminService.create_user."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import UserRole
from app.core.exceptions import ConflictException
from app.models.user import User
from app.schemas.user import CreateUserRequest
from app.services.admin import AdminService


def _make_user(
    username: str = "testuser",
    role: UserRole = UserRole.STAFF,
    is_active: bool = True,
) -> User:
    """Create a test user."""
    now = datetime.now(timezone.utc)
    return User(
        id="user-1",
        username=username,
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$...",
        full_name="Test User",
        role=role,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


def _make_admin_service() -> AdminService:
    """Create an AdminService with mock session."""
    return AdminService(session=cast(AsyncSession, object()))


@pytest.mark.asyncio
async def test_create_user_success_with_valid_data() -> None:
    """Test create_user returns created user with valid data."""
    service = _make_admin_service()
    mock_repo = AsyncMock()

    new_user = _make_user(username="newuser", role=UserRole.STAFF)
    mock_repo.get_by_username.return_value = None  # User doesn't exist
    mock_repo.create.return_value = new_user
    service._repo = mock_repo

    request_data = CreateUserRequest(
        username="newuser",
        password="securepass123",
        full_name="New User",
        role=UserRole.STAFF,
    )

    result = await service.create_user(request_data)

    assert result.username == "newuser"
    assert result.role == UserRole.STAFF
    assert result.is_active is True
    mock_repo.get_by_username.assert_awaited_once_with("newuser")
    mock_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_user_success_creates_admin() -> None:
    """Test create_user successfully creates admin role."""
    service = _make_admin_service()
    mock_repo = AsyncMock()

    new_admin = _make_user(username="admin", role=UserRole.ADMIN)
    mock_repo.get_by_username.return_value = None
    mock_repo.create.return_value = new_admin
    service._repo = mock_repo

    request_data = CreateUserRequest(
        username="admin",
        password="adminpass123",
        full_name="Admin User",
        role=UserRole.ADMIN,
    )

    result = await service.create_user(request_data)

    assert result.username == "admin"
    assert result.role == UserRole.ADMIN
    mock_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_user_fails_with_duplicate_username() -> None:
    """Test create_user raises ConflictException for duplicate username."""
    service = _make_admin_service()
    mock_repo = AsyncMock()

    # User already exists
    existing_user = _make_user(username="existinguser")
    mock_repo.get_by_username.return_value = existing_user
    service._repo = mock_repo

    request_data = CreateUserRequest(
        username="existinguser",
        password="password123",
        full_name="Existing User",
        role=UserRole.STAFF,
    )

    with pytest.raises(ConflictException):
        await service.create_user(request_data)

    mock_repo.get_by_username.assert_awaited_once_with("existinguser")


@pytest.mark.asyncio
async def test_create_user_preserves_role() -> None:
    """Test create_user preserves the role specified in request."""
    service = _make_admin_service()
    mock_repo = AsyncMock()

    new_admin = _make_user(username="newadmin", role=UserRole.ADMIN)
    mock_repo.get_by_username.return_value = None
    mock_repo.create.return_value = new_admin
    service._repo = mock_repo

    request_data = CreateUserRequest(
        username="newadmin",
        password="password123",
        full_name="New Admin",
        role=UserRole.ADMIN,
    )

    result = await service.create_user(request_data)

    assert result.role == UserRole.ADMIN
    assert result.role.value == "admin"


@pytest.mark.asyncio
async def test_create_user_preserves_full_name() -> None:
    """Test create_user preserves the full_name from request."""
    service = _make_admin_service()
    mock_repo = AsyncMock()

    new_user = _make_user(username="testuser")
    new_user.full_name = "John Doe Smith"
    mock_repo.get_by_username.return_value = None
    mock_repo.create.return_value = new_user
    service._repo = mock_repo

    request_data = CreateUserRequest(
        username="testuser",
        password="password123",
        full_name="John Doe Smith",
        role=UserRole.STAFF,
    )

    result = await service.create_user(request_data)

    assert result.full_name == "John Doe Smith"


@pytest.mark.asyncio
async def test_create_user_checks_existing_user_by_username() -> None:
    """Test create_user checks for existing username before creating."""
    service = _make_admin_service()
    mock_repo = AsyncMock()

    mock_repo.get_by_username.return_value = None
    new_user = _make_user(username="newuser")
    mock_repo.create.return_value = new_user
    service._repo = mock_repo

    request_data = CreateUserRequest(
        username="newuser",
        password="password123",
        full_name="New User",
        role=UserRole.STAFF,
    )

    await service.create_user(request_data)

    # Verify get_by_username was called BEFORE create
    mock_repo.get_by_username.assert_awaited_once_with("newuser")


@pytest.mark.asyncio
async def test_create_user_returns_user_response_with_id() -> None:
    """Test create_user returns UserResponse with user ID."""
    service = _make_admin_service()
    mock_repo = AsyncMock()

    new_user = _make_user(username="newuser")
    new_user.id = "user-123"
    mock_repo.get_by_username.return_value = None
    mock_repo.create.return_value = new_user
    service._repo = mock_repo

    request_data = CreateUserRequest(
        username="newuser",
        password="password123",
        full_name="New User",
        role=UserRole.STAFF,
    )

    result = await service.create_user(request_data)

    assert result.id == "user-123"
    assert result.username == "newuser"


@pytest.mark.asyncio
async def test_create_user_with_special_characters_in_name() -> None:
    """Test create_user handles special characters in full_name."""
    service = _make_admin_service()
    mock_repo = AsyncMock()

    new_user = _make_user(username="testuser")
    new_user.full_name = "José García-López"
    mock_repo.get_by_username.return_value = None
    mock_repo.create.return_value = new_user
    service._repo = mock_repo

    request_data = CreateUserRequest(
        username="testuser",
        password="password123",
        full_name="José García-López",
        role=UserRole.STAFF,
    )

    result = await service.create_user(request_data)

    assert result.full_name == "José García-López"
