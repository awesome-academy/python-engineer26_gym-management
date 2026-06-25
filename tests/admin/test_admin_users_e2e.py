"""End-to-end tests for admin user creation endpoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
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


def _build_test_client(user: User) -> TestClient:
    """Build test client with mocked dependencies."""
    app = create_app()

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.router.lifespan_context = _noop_lifespan

    # Override get_db to prevent real database access
    async def mock_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user] = lambda: user

    return TestClient(app)


def test_create_user_endpoint_returns_201_for_admin() -> None:
    """Test create_user endpoint returns 201 Created for admin."""
    current_admin = _make_user(username="admin", role=UserRole.ADMIN)

    async def mock_create_user(request):
        new_user = _make_user(username="newuser", role=UserRole.STAFF, is_active=True)
        return new_user

    with patch("app.api.v1.admin.users.AdminService") as MockAdminService:
        mock_service = AsyncMock()
        mock_service.create_user = mock_create_user
        MockAdminService.return_value = mock_service

        with _build_test_client(current_admin) as client:
            response = client.post(
                "/api/v1/admin/users/",
                json={
                    "username": "newuser",
                    "password": "securepass123",
                    "full_name": "New User",
                    "role": "staff",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "staff"
    assert data["is_active"] is True


def test_create_user_endpoint_returns_403_for_staff() -> None:
    """Test create_user endpoint returns 403 Forbidden for staff."""
    current_staff = _make_user(username="staff", role=UserRole.STAFF)

    with _build_test_client(current_staff) as client:
        response = client.post(
            "/api/v1/admin/users/",
            json={
                "username": "newuser",
                "password": "securepass123",
                "full_name": "New User",
                "role": "staff",
            },
        )

    assert response.status_code == 403
    data = response.json()
    assert "message" in data or "detail" in data


def test_create_user_endpoint_returns_401_without_auth() -> None:
    app = create_app()

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.router.lifespan_context = _noop_lifespan

    async def mock_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = mock_get_db

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/admin/users/",
            json={
                "username": "newuser",
                "password": "securepass123",
                "full_name": "New User",
                "role": "staff",
            },
        )

    assert response.status_code == 401


def test_create_user_endpoint_returns_422_with_invalid_role() -> None:
    """Test create_user endpoint returns 422 with invalid role."""
    current_admin = _make_user(username="admin", role=UserRole.ADMIN)

    with _build_test_client(current_admin) as client:
        response = client.post(
            "/api/v1/admin/users/",
            json={
                "username": "newuser",
                "password": "securepass123",
                "full_name": "New User",
                "role": "invalid_role",
            },
        )

    assert response.status_code == 422


def test_create_user_endpoint_returns_422_with_missing_username() -> None:
    """Test create_user endpoint returns 422 with missing username."""
    current_admin = _make_user(username="admin", role=UserRole.ADMIN)

    with _build_test_client(current_admin) as client:
        response = client.post(
            "/api/v1/admin/users/",
            json={
                "password": "securepass123",
                "full_name": "New User",
                "role": "staff",
            },
        )

    assert response.status_code == 422


def test_create_user_endpoint_returns_422_with_missing_password() -> None:
    """Test create_user endpoint returns 422 with missing password."""
    current_admin = _make_user(username="admin", role=UserRole.ADMIN)

    with _build_test_client(current_admin) as client:
        response = client.post(
            "/api/v1/admin/users/",
            json={
                "username": "newuser",
                "full_name": "New User",
                "role": "staff",
            },
        )

    assert response.status_code == 422


def test_create_user_endpoint_returns_422_with_missing_full_name() -> None:
    """Test create_user endpoint returns 422 with missing full_name."""
    current_admin = _make_user(username="admin", role=UserRole.ADMIN)

    with _build_test_client(current_admin) as client:
        response = client.post(
            "/api/v1/admin/users/",
            json={
                "username": "newuser",
                "password": "securepass123",
                "role": "staff",
            },
        )

    assert response.status_code == 422


def test_create_user_endpoint_returns_422_with_missing_role() -> None:
    """Test create_user endpoint returns 422 with missing role."""
    current_admin = _make_user(username="admin", role=UserRole.ADMIN)

    with _build_test_client(current_admin) as client:
        response = client.post(
            "/api/v1/admin/users/",
            json={
                "username": "newuser",
                "password": "securepass123",
                "full_name": "New User",
            },
        )

    assert response.status_code == 422


def test_create_user_endpoint_returns_409_for_duplicate_username() -> None:
    """Test create_user endpoint returns 409 Conflict for duplicate username."""
    current_admin = _make_user(username="admin", role=UserRole.ADMIN)

    from app.core.exceptions import ConflictException

    async def mock_create_user_duplicate(request):
        raise ConflictException("Username already exists")

    with patch("app.api.v1.admin.users.AdminService") as MockAdminService:
        mock_service = AsyncMock()
        mock_service.create_user = mock_create_user_duplicate
        MockAdminService.return_value = mock_service

        with _build_test_client(current_admin) as client:
            response = client.post(
                "/api/v1/admin/users/",
                json={
                    "username": "existinguser",
                    "password": "securepass123",
                    "full_name": "Existing User",
                    "role": "staff",
                },
            )

    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data.get("message", "")


def test_create_user_endpoint_returns_admin_role() -> None:
    """Test create_user endpoint can create admin role."""
    current_admin = _make_user(username="admin", role=UserRole.ADMIN)

    async def mock_create_admin(request):
        new_admin = _make_user(username="newadmin", role=UserRole.ADMIN, is_active=True)
        return new_admin

    with patch("app.api.v1.admin.users.AdminService") as MockAdminService:
        mock_service = AsyncMock()
        mock_service.create_user = mock_create_admin
        MockAdminService.return_value = mock_service

        with _build_test_client(current_admin) as client:
            response = client.post(
                "/api/v1/admin/users/",
                json={
                    "username": "newadmin",
                    "password": "securepass123",
                    "full_name": "New Admin",
                    "role": "admin",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newadmin"
    assert data["role"] == "admin"


def test_create_user_response_excludes_password_hash() -> None:
    """Test create_user response does not include password_hash."""
    current_admin = _make_user(username="admin", role=UserRole.ADMIN)

    async def mock_create_user(request):
        new_user = _make_user(username="newuser", role=UserRole.STAFF, is_active=True)
        return new_user

    with patch("app.api.v1.admin.users.AdminService") as MockAdminService:
        mock_service = AsyncMock()
        mock_service.create_user = mock_create_user
        MockAdminService.return_value = mock_service

        with _build_test_client(current_admin) as client:
            response = client.post(
                "/api/v1/admin/users/",
                json={
                    "username": "newuser",
                    "password": "securepass123",
                    "full_name": "New User",
                    "role": "staff",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert "password_hash" not in data
    assert "password" not in data
