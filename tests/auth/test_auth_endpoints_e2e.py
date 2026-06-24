from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.enum import UserRole
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.main import create_app
from app.models.user import User


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


def _build_test_client(user: User | None = None) -> TestClient:
    app = create_app()

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.router.lifespan_context = _noop_lifespan

    async def mock_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = mock_get_db

    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user

    return TestClient(app)


def test_login_endpoint_success_with_valid_credentials() -> None:
    """Test login endpoint returns 200 with valid credentials."""

    # Mock AuthService.login to return tokens
    async def mock_login(request):
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

    with patch("app.api.v1.auth.AuthService") as MockAuthService:
        mock_service = AsyncMock()
        mock_service.login = mock_login
        MockAuthService.return_value = mock_service

        with _build_test_client() as client:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "test_access_token"
    assert data["token_type"] == "bearer"


def test_login_endpoint_returns_401_with_invalid_username() -> None:
    """Test login endpoint returns 401 with invalid username."""
    # Mock AuthService.login to raise UnauthorizedException
    from app.core.exceptions import UnauthorizedException

    async def mock_login(request):
        raise UnauthorizedException("Invalid username or password")

    with patch("app.api.v1.auth.AuthService") as MockAuthService:
        mock_service = AsyncMock()
        mock_service.login = mock_login
        MockAuthService.return_value = mock_service

        with _build_test_client() as client:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "nonexistent", "password": "password"},
            )

    assert response.status_code == 401
    data = response.json()
    assert "Invalid username or password" in data.get("message", "")


def test_login_endpoint_returns_401_with_wrong_password() -> None:
    """Test login endpoint returns 401 with wrong password."""
    from app.core.exceptions import UnauthorizedException

    async def mock_login(request):
        raise UnauthorizedException("Invalid username or password")

    with patch("app.api.v1.auth.AuthService") as MockAuthService:
        mock_service = AsyncMock()
        mock_service.login = mock_login
        MockAuthService.return_value = mock_service

        with _build_test_client() as client:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "wrongpassword"},
            )

    assert response.status_code == 401


def test_login_endpoint_returns_401_for_inactive_user() -> None:
    """Test login endpoint returns 401 for inactive users."""
    from app.core.exceptions import UnauthorizedException

    async def mock_login(request):
        raise UnauthorizedException("Invalid username or password")

    with patch("app.api.v1.auth.AuthService") as MockAuthService:
        mock_service = AsyncMock()
        mock_service.login = mock_login
        MockAuthService.return_value = mock_service

        with _build_test_client() as client:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "inactive", "password": "password123"},
            )

    assert response.status_code == 401


def test_login_endpoint_returns_422_with_missing_username() -> None:
    """Test login endpoint returns 422 when username is missing."""
    with _build_test_client() as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "password123"},
        )

    assert response.status_code == 422


def test_login_endpoint_returns_422_with_missing_password() -> None:
    """Test login endpoint returns 422 when password is missing."""
    with _build_test_client() as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin"},
        )

    assert response.status_code == 422


def test_logout_endpoint_returns_204_for_authenticated_user() -> None:
    """Test logout endpoint returns 204 for authenticated user."""
    current_user = _make_user(username="admin", role=UserRole.ADMIN)

    async def mock_logout(access_token, refresh_token):
        pass

    with patch("app.api.v1.auth.AuthService") as MockAuthService:
        mock_service = AsyncMock()
        mock_service.logout = mock_logout
        MockAuthService.return_value = mock_service

        with _build_test_client(current_user) as client:
            response = client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": "Bearer test_token"},
                cookies={"refresh_token": "test_refresh_token"},
            )

    assert response.status_code == 204


def test_logout_endpoint_returns_401_without_authorization() -> None:
    """Test logout endpoint returns 401 without authorization header."""
    with _build_test_client() as client:
        response = client.post("/api/v1/auth/logout")

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data or "message" in data


def test_logout_endpoint_returns_401_with_invalid_token() -> None:
    """Test logout endpoint returns 401 with invalid token."""
    with _build_test_client() as client:
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid_token"},
        )

    assert response.status_code == 401
    data = response.json()
    assert "message" in data or "detail" in data


def test_logout_endpoint_returns_401_with_missing_refresh_token() -> None:
    """Test logout endpoint returns 401 when refresh token is missing."""
    current_user = _make_user(username="admin", role=UserRole.ADMIN)

    with _build_test_client(current_user) as client:
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer test_token"},
        )

    assert response.status_code == 401
    data = response.json()
    assert "message" in data or "detail" in data


def test_refresh_token_in_login_response_is_sent() -> None:
    """Test that refresh token is sent in login response."""

    async def mock_login(request):
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

    with patch("app.api.v1.auth.AuthService") as MockAuthService:
        mock_service = AsyncMock()
        mock_service.login = mock_login
        MockAuthService.return_value = mock_service

        with _build_test_client() as client:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"},
            )

    assert response.status_code == 200
    assert "refresh_token" in response.cookies
