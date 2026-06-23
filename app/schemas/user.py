from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core import UserRole


class CreateUserRequest(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=50, description="Username for the user"
    )
    password: str = Field(
        ..., min_length=6, description="Password for the user (will be hashed)"
    )
    full_name: str = Field(
        ..., min_length=1, max_length=100, description="Full name of the user"
    )
    role: UserRole = Field(default=UserRole.STAFF, description="Role of the user")
    is_active: bool = Field(default=True, description="Whether the user is active")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
