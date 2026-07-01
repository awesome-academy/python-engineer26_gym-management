from __future__ import annotations

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import CREATE_USER_REQUEST_EXAMPLES, responses_for
from app.dependencies.auth import require_admin
from app.dependencies.database import get_db
from app.models import User
from app.schemas import CreateUserRequest, UserResponse
from app.services.admin import AdminService

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an admin-managed user",
    description="Create a new system user through an administrator-only endpoint.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def create_user(
    user_data: CreateUserRequest = Body(
        ..., openapi_examples=CREATE_USER_REQUEST_EXAMPLES
    ),
    session: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> UserResponse:
    return await AdminService(session).create_user(user_data)
