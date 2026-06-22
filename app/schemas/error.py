from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ErrorCode(str, Enum):
    BAD_REQUEST = "bad_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    VALIDATION_ERROR = "validation_error"


class FieldError(BaseModel):
    field: str
    message: str
    code: str = "error"


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ValidationErrorResponse(BaseModel):
    code: str
    message: str
    errors: list[FieldError]
