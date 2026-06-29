"""End-to-end tests for member endpoints."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from contextlib import asynccontextmanager

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.main import create_app
from app.models.member import Member
from app.models.user import User
from app.schemas.common import PaginatedResponse


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


def _build_test_client() -> TestClient:
    app = create_app()

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.router.lifespan_context = _noop_lifespan

    # Override get_db to prevent real database access
    async def mock_get_db():
        yield AsyncMock()

    # Create a mock current_user
    mock_user = User(
        id="user-1",
        username="testuser",
        password_hash="hashed",
        full_name="Test User",
        role="STAFF",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    async def mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_current_user] = mock_get_current_user

    return TestClient(app)


def test_create_member_endpoint_returns_201_for_valid_data() -> None:
    """Test create_member endpoint returns 201 Created with valid data."""
    new_member = _make_member(phone="0901234567", full_name="John Doe", gender="Male")

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.create = AsyncMock(return_value=new_member)
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.post(
                "/api/v1/members",
                json={
                    "phone": "0901234567",
                    "full_name": "John Doe",
                    "gender": "Male",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["phone"] == "0901234567"
    assert data["full_name"] == "John Doe"
    assert data["gender"] == "Male"


def test_create_member_endpoint_returns_422_with_invalid_phone() -> None:
    """Test create_member endpoint returns 422 with invalid phone."""
    with _build_test_client() as client:
        response = client.post(
            "/api/v1/members",
            json={
                "phone": "",
                "full_name": "John Doe",
            },
        )

    assert response.status_code == 422


def test_create_member_endpoint_returns_422_with_missing_phone() -> None:
    """Test create_member endpoint returns 422 with missing phone."""
    with _build_test_client() as client:
        response = client.post(
            "/api/v1/members",
            json={
                "full_name": "John Doe",
            },
        )

    assert response.status_code == 422


def test_create_member_endpoint_returns_422_with_missing_full_name() -> None:
    """Test create_member endpoint returns 422 with missing full_name."""
    with _build_test_client() as client:
        response = client.post(
            "/api/v1/members",
            json={
                "phone": "0901234567",
            },
        )

    assert response.status_code == 422


def test_create_member_endpoint_returns_409_for_duplicate_phone() -> None:
    """Test create_member endpoint returns 409 Conflict for duplicate phone."""
    from app.core.exceptions import ConflictException

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.create = AsyncMock(
            side_effect=ConflictException("Phone number '0901234567' already exists")
        )
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.post(
                "/api/v1/members",
                json={
                    "phone": "0901234567",
                    "full_name": "John Doe",
                },
            )

    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data.get("message", "")


def test_get_members_endpoint_returns_paginated_list() -> None:
    """Test get_members endpoint returns paginated list."""
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

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.get_list = AsyncMock(return_value=paginated)
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.get("/api/v1/members")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert data["page"] == 1


def test_get_members_endpoint_filters_by_phone() -> None:
    """Test get_members endpoint filters by phone."""
    member = _make_member(phone="0901234567")

    paginated = PaginatedResponse(
        items=[member],
        total=1,
        page=1,
        limit=10,
    )

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.get_list = AsyncMock(return_value=paginated)
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.get("/api/v1/members?phone=0901234567")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["phone"] == "0901234567"


def test_get_members_endpoint_filters_by_full_name() -> None:
    """Test get_members endpoint filters by full_name."""
    member = _make_member(full_name="John")

    paginated = PaginatedResponse(
        items=[member],
        total=1,
        page=1,
        limit=10,
    )

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.get_list = AsyncMock(return_value=paginated)
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.get("/api/v1/members?full_name=John")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["full_name"] == "John"


def test_create_member_response_contains_all_fields() -> None:
    """Test create_member response includes all member fields."""
    new_member = _make_member(
        phone="0901234567",
        full_name="John Doe",
        date_of_birth=date(1990, 1, 1),
        gender="Male",
    )

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.create = AsyncMock(return_value=new_member)
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.post(
                "/api/v1/members",
                json={
                    "phone": "0901234567",
                    "full_name": "John Doe",
                    "date_of_birth": "1990-01-01",
                    "gender": "Male",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "phone" in data
    assert "full_name" in data
    assert "date_of_birth" in data
    assert "gender" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_member_endpoint_returns_200_for_valid_id() -> None:
    """Test get_member endpoint returns 200 with valid member id."""
    member = _make_member(phone="0901234567", full_name="John Doe")

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.get = AsyncMock(return_value=member)
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.get("/api/v1/members/member-1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "member-1"
    assert data["phone"] == "0901234567"
    assert data["full_name"] == "John Doe"
    assert "subscription_history" in data
    assert data["subscription_history"]["items"] == []


def test_get_member_endpoint_returns_404_for_invalid_id() -> None:
    """Test get_member endpoint returns 404 for non-existent member."""
    from app.core.exceptions import NotFoundException

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.get = AsyncMock(side_effect=NotFoundException("Member not found"))
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.get("/api/v1/members/invalid-id")

    assert response.status_code == 404


def test_update_member_endpoint_returns_200_for_valid_data() -> None:
    """Test update_member endpoint returns 200 with valid data."""
    updated_member = _make_member(
        phone="0909999999",
        full_name="Updated Name",
        gender="Female",
    )

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.update = AsyncMock(return_value=updated_member)
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.put(
                "/api/v1/members/member-1",
                json={
                    "phone": "0909999999",
                    "full_name": "Updated Name",
                    "gender": "Female",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "0909999999"
    assert data["full_name"] == "Updated Name"
    assert data["gender"] == "Female"


def test_update_member_endpoint_returns_404_for_invalid_id() -> None:
    """Test update_member endpoint returns 404 for non-existent member."""
    from app.core.exceptions import NotFoundException

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.update = AsyncMock(
            side_effect=NotFoundException("Member not found")
        )
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.put(
                "/api/v1/members/invalid-id",
                json={"full_name": "New Name"},
            )

    assert response.status_code == 404


def test_update_member_endpoint_returns_409_for_duplicate_phone() -> None:
    """Test update_member endpoint returns 409 when phone already exists."""
    from app.core.exceptions import ConflictException

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.update = AsyncMock(
            side_effect=ConflictException("Phone number already exists")
        )
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.put(
                "/api/v1/members/member-1",
                json={"phone": "0901111111"},
            )

    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data.get("message", "")


def test_update_member_endpoint_partial_update() -> None:
    """Test update_member endpoint with partial data."""
    updated_member = _make_member(
        phone="0901234567",  # unchanged
        full_name="Updated Name Only",  # changed
    )

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.update = AsyncMock(return_value=updated_member)
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.put(
                "/api/v1/members/member-1",
                json={"full_name": "Updated Name Only"},  # Only this field
            )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name Only"
    assert data["phone"] == "0901234567"  # Unchanged


def test_delete_member_endpoint_returns_204_for_valid_id() -> None:
    """Test delete_member endpoint returns 204 No Content for valid id."""
    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.delete = AsyncMock(return_value=None)
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.delete("/api/v1/members/member-1")

    assert response.status_code == 204


def test_delete_member_endpoint_returns_404_for_invalid_id() -> None:
    """Test delete_member endpoint returns 404 for non-existent member."""
    from app.core.exceptions import NotFoundException

    with patch("app.api.v1.member.MemberService") as MockService:
        mock_service = AsyncMock()
        mock_service.delete = AsyncMock(
            side_effect=NotFoundException("Member not found")
        )
        MockService.return_value = mock_service

        with _build_test_client() as client:
            response = client.delete("/api/v1/members/invalid-id")

    assert response.status_code == 404
