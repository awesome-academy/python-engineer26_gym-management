from __future__ import annotations

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enum import UserRole
from app.models.base import Base


class User(Base):
    """User model for gym staff"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.STAFF,
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
