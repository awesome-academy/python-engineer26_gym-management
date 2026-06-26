from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import cast
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enum import SubscriptionStatus, UserRole
from app.dependencies.auth import get_current_user
from app.dependencies.subscription import get_subscription_service
from app.main import create_app
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.subscription import SubscriptionResponse
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


def _build_test_client(service: SubscriptionService, user: User) -> TestClient:
    app = create_app()

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.router.lifespan_context = _noop_lifespan
    app.dependency_overrides[get_subscription_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: user

    return TestClient(app)


def test_create_subscription_endpoint_returns_201() -> None:
    service = _make_service()
    mock_create = AsyncMock(
        return_value=SubscriptionResponse(
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
    )
    service.create = mock_create  # type: ignore[method-assign]

    with _build_test_client(service, _make_user()) as client:
        response = client.post(
            "/api/v1/subscriptions",
            json={
                "member_id": "member-1",
                "package_id": "package-1",
                "start_date": "2026-06-01",
                "end_date": "2026-07-01",
                "status": "pending",
                "price": 499000,
                "sold_by": "user-2",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "sub-1"
    assert data["created_by"] == "user-1"
    assert data["member_id"] == "member-1"
    assert data["price"] == 499000.0


def test_get_subscriptions_endpoint_accepts_optional_dates() -> None:
    service = _make_service()
    mock_get_list = AsyncMock(
        return_value=PaginatedResponse[SubscriptionResponse](
            items=[],
            total=0,
            page=1,
            limit=10,
        )
    )
    service.get_list = mock_get_list  # type: ignore[method-assign]

    with _build_test_client(service, _make_user()) as client:
        response = client.get("/api/v1/subscriptions?page=1&limit=10")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "page": 1,
        "limit": 10,
    }


def test_get_subscriptions_endpoint_filters() -> None:
    service = _make_service()
    mock_get_list = AsyncMock(
        return_value=PaginatedResponse[SubscriptionResponse](
            items=[
                SubscriptionResponse(
                    id="sub-1",
                    member_id="member-1",
                    package_id="package-1",
                    start_date=date(2026, 6, 1),
                    end_date=date(2026, 7, 1),
                    status=SubscriptionStatus.ACTIVE,
                    price=499000.0,
                    created_by="user-1",
                    sold_by="user-2",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            ],
            total=1,
            page=1,
            limit=10,
        )
    )
    service.get_list = mock_get_list  # type: ignore[method-assign]

    with _build_test_client(service, _make_user()) as client:
        response = client.get(
            "/api/v1/subscriptions"
            "?member_id=member-1"
            "&status=active"
            "&package_id=package-1"
            "&start_date=2026-06-01"
            "&end_date=2026-07-01"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "sub-1"
    assert data["items"][0]["status"] == "active"
    assert data["items"][0]["price"] == 499000.0
