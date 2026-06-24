"""Unit tests for AuthService."""

from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import UserRole
from app.core.exceptions import UnauthorizedException
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.services.auth import AuthService


def _make_user(
    username: str = "testuser",
    role: UserRole = UserRole.STAFF,
    is_active: bool = True,
) -> User:
    """Create a test user."""
    return User(
        id="user-1",
        username=username,
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$...",
        full_name="Test User",
        role=role,
        is_active=is_active,
    )


def _make_service() -> AuthService:
    """Create an AuthService with mock session."""
    return AuthService(session=cast(AsyncSession, object()))


@pytest.mark.asyncio
async def test_login_success_with_valid_credentials() -> None:
    """Test login succeeds with correct username and password."""
    service = _make_service()
    mock_repo = AsyncMock()

    user = _make_user(username="admin", role=UserRole.ADMIN, is_active=True)
    mock_repo.get_by_username.return_value = user
    service._repo = mock_repo

    # Mock password verification to return True
    with patch("app.services.auth.verify_password", return_value=True):
        with patch(
            "app.services.auth.create_access_token", return_value="access_token"
        ):
            with patch(
                "app.services.auth.create_refresh_token", return_value="refresh_token"
            ):
                result = await service.login(
                    LoginRequest(username="admin", password="admin123")
                )

    assert result["access_token"] == "access_token"
    assert result["refresh_token"] == "refresh_token"
    mock_repo.get_by_username.assert_awaited_once_with("admin")


@pytest.mark.asyncio
async def test_login_fail_with_invalid_username() -> None:
    """Test login fails when username doesn't exist."""
    service = _make_service()
    mock_repo = AsyncMock()
    mock_repo.get_by_username.return_value = None
    service._repo = mock_repo

    with pytest.raises(UnauthorizedException, match="Invalid username or password"):
        await service.login(LoginRequest(username="nonexistent", password="password"))

    mock_repo.get_by_username.assert_awaited_once_with("nonexistent")


@pytest.mark.asyncio
async def test_login_fail_with_invalid_password() -> None:
    """Test login fails when password is incorrect."""
    service = _make_service()
    mock_repo = AsyncMock()

    user = _make_user(username="admin")
    mock_repo.get_by_username.return_value = user
    service._repo = mock_repo

    with patch("app.services.auth.verify_password", return_value=False):
        with pytest.raises(UnauthorizedException, match="Invalid username or password"):
            await service.login(LoginRequest(username="admin", password="wrongpass"))

    mock_repo.get_by_username.assert_awaited_once_with("admin")


@pytest.mark.asyncio
async def test_login_fail_with_inactive_user() -> None:
    """Test login fails when user account is inactive."""
    service = _make_service()
    mock_repo = AsyncMock()

    user = _make_user(username="admin", is_active=False)
    mock_repo.get_by_username.return_value = user
    service._repo = mock_repo

    with patch("app.services.auth.verify_password", return_value=True):
        with pytest.raises(UnauthorizedException, match="Invalid username or password"):
            await service.login(LoginRequest(username="admin", password="admin123"))

    mock_repo.get_by_username.assert_awaited_once_with("admin")


@pytest.mark.asyncio
async def test_login_staff_role() -> None:
    """Test login works for staff users."""
    service = _make_service()
    mock_repo = AsyncMock()

    user = _make_user(username="staff", role=UserRole.STAFF, is_active=True)
    mock_repo.get_by_username.return_value = user
    service._repo = mock_repo

    with patch("app.services.auth.verify_password", return_value=True):
        with patch(
            "app.services.auth.create_access_token", return_value="access_token"
        ):
            with patch(
                "app.services.auth.create_refresh_token", return_value="refresh_token"
            ):
                result = await service.login(
                    LoginRequest(username="staff", password="staff123")
                )

    assert result["access_token"] == "access_token"
    assert result["refresh_token"] == "refresh_token"


@pytest.mark.asyncio
async def test_logout_revokes_both_tokens() -> None:
    """Test logout revokes both access and refresh tokens."""
    service = _make_service()

    with patch("app.services.auth.revoke_token") as mock_revoke:
        await service.logout(
            access_token="access_token_123",
            refresh_token="refresh_token_456",
        )

    # Verify revoke_token was called twice - once for each token
    assert mock_revoke.call_count == 2
    call_args_list = mock_revoke.call_args_list
    assert call_args_list[0][0][0] == "access_token_123"
    assert call_args_list[1][0][0] == "refresh_token_456"


@pytest.mark.asyncio
async def test_logout_with_empty_tokens() -> None:
    """Test logout handles empty tokens gracefully."""
    service = _make_service()

    with patch("app.services.auth.revoke_token") as mock_revoke:
        await service.logout(
            access_token="",
            refresh_token="",
        )

    # Should still call revoke_token for both
    assert mock_revoke.call_count == 2
