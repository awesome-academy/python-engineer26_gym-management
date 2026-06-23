from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import UserRole
from app.dependencies.auth import get_current_user
from app.dependencies.package import get_package_service
from app.main import create_app
from app.models.user import User
from app.schemas.common import PaginatedResponse
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


def _build_test_client(service: PackageService, user: User | None = None) -> TestClient:
    app = create_app()

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.router.lifespan_context = _noop_lifespan
    app.dependency_overrides[get_package_service] = lambda: service
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user

    return TestClient(app)


@pytest.mark.asyncio
async def test_create_package_endpoint_returns_201_for_admin() -> None:
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

    with _build_test_client(service, _make_user(UserRole.ADMIN)) as client:
        response = client.post(
            "/api/v1/packages",
            json={
                "name": "Premium",
                "description": "Full access",
                "price": 499000,
                "duration": 30,
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "id": "pkg-1",
        "name": "Premium",
        "description": "Full access",
        "price": 499000.0,
        "duration": 30,
    }


@pytest.mark.asyncio
async def test_create_package_endpoint_returns_403_for_staff() -> None:
    service = _make_service()
    service._repo = AsyncMock()

    with _build_test_client(service, _make_user(UserRole.STAFF)) as client:
        response = client.post(
            "/api/v1/packages",
            json={
                "name": "Premium",
                "description": "Full access",
                "price": 499000,
                "duration": 30,
            },
        )

    assert response.status_code == 403
    assert response.json()["message"] == "Only admin users can create packages"


@pytest.mark.asyncio
async def test_get_packages_endpoint_returns_paginated_data() -> None:
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

    with _build_test_client(service) as client:
        response = client.get("/api/v1/packages?name=%20premium%20&limit=10&page=1")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": "pkg-1",
                "name": "Premium",
                "description": "Full access",
                "price": 499000.0,
                "duration": 30,
            }
        ],
        "total": 1,
        "page": 1,
        "limit": 10,
    }
