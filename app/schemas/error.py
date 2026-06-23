from __future__ import annotations

from pydantic import BaseModel


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
