from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.dependencies.database import get_db
from app.models import User
from app.schemas import CreateUserRequest, UserResponse
from app.services.admin import AdminService

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: CreateUserRequest,
    session: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> UserResponse:
    return await AdminService(session).create_user(user_data)
