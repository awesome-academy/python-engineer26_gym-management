from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException
from app.core.security import hash_password
from app.repositories import UserRepository
from app.schemas import CreateUserRequest, UserResponse


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    async def create_user(self, data: CreateUserRequest) -> UserResponse:
        existing_user = await self._repo.get_by_username(data.username)
        if existing_user:
            raise ConflictException(
                message=f"Username '{data.username}' already exists"
            )

        try:
            new_user = await self._repo.create(
                username=data.username,
                password_hash=hash_password(data.password),
                full_name=data.full_name,
                role=data.role,
                is_active=data.is_active,
            )
            await self._repo.session.flush()
        except IntegrityError as e:
            await self._repo.session.rollback()
            raise ConflictException(
                message=f"Username '{data.username}' already exists"
            ) from e

        return UserResponse.model_validate(new_user)
