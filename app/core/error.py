from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    BAD_REQUEST = "bad_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    VALIDATION_ERROR = "validation_error"
    INVALID_CREDENTIALS = "invalid_credentials"
    INVALID_TOKEN = "invalid_token"
