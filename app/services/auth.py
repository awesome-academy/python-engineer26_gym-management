from __future__ import annotations
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.redis import revoke_token
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.repositories import UserRepository
from app.schemas import LoginRequest
from app.core import ErrorCode, settings


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    async def login(self, data: LoginRequest) -> dict[str, str]:
        user = await self._repo.get_by_username(data.username)
        if (
            not user
            or not verify_password(data.password, user.password_hash)
            or not user.is_active
        ):
            raise UnauthorizedException(
                message="Invalid username or password",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
        }

    async def logout(self, access_token: str, refresh_token: str) -> None:
        await revoke_token(
            access_token,
            timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        await revoke_token(
            refresh_token,
            timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
