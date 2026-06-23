from __future__ import annotations

import logging

from app.core.config import settings
from app.core.database import AsyncSessionFactory
from app.core.enum import UserRole
from app.core.security import hash_password
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


async def initialize_super_admin() -> None:
    # Skip initialization if password not provided via environment variable
    if settings.SUPER_ADMIN_PASSWORD is None:
        logger.info("SUPER_ADMIN_PASSWORD not set; skipping auto-initialization")
        return

    password = settings.SUPER_ADMIN_PASSWORD

    async with AsyncSessionFactory() as session:
        try:
            user_repo = UserRepository(session)

            existing_admin = await user_repo.get_by_username(
                settings.SUPER_ADMIN_USERNAME
            )

            if existing_admin:
                logger.info("Super admin already exists")
                return

            admin_user = await user_repo.create(
                username=settings.SUPER_ADMIN_USERNAME,
                password_hash=hash_password(password),
                full_name="Super Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )

            await session.commit()
            logger.info("Super admin created successfully: %s", admin_user.username)

        except Exception as e:
            await session.rollback()
            logger.error("Failed to initialize super admin: %s", e, exc_info=True)
            raise
