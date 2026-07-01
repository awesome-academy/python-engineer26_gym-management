from __future__ import annotations

from typing import Any

from fastapi import status
from fastapi.openapi.models import Example

from app.schemas import ErrorResponse, ValidationErrorResponse

OpenAPIStatusCode = int | str
OpenAPIResponseSpec = dict[str, Any]


OPENAPI_RESPONSES: dict[OpenAPIStatusCode, OpenAPIResponseSpec] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Authentication is required or the provided token is invalid.",
        "content": {
            "application/json": {
                "example": {
                    "code": "unauthorized",
                    "message": "Not authenticated",
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": "The current user does not have permission to perform this action.",
        "content": {
            "application/json": {
                "example": {
                    "code": "forbidden",
                    "message": "Insufficient permissions",
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "The requested resource does not exist.",
        "content": {
            "application/json": {
                "example": {
                    "code": "not_found",
                    "message": "Resource not found",
                }
            }
        },
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "model": ValidationErrorResponse,
        "description": "The request payload or query parameters failed validation.",
        "content": {
            "application/json": {
                "example": {
                    "code": "validation_error",
                    "message": "Validation error",
                    "errors": [
                        {
                            "field": "username",
                            "message": "Field required",
                            "code": "missing",
                        }
                    ],
                }
            }
        },
    },
}


def responses_for(
    *status_codes: OpenAPIStatusCode,
) -> dict[OpenAPIStatusCode, OpenAPIResponseSpec]:
    return {
        status_code: OPENAPI_RESPONSES[status_code]
        for status_code in status_codes
        if status_code in OPENAPI_RESPONSES
    }


LOGIN_REQUEST_EXAMPLES: dict[str, Example] = {
    "staff_login": Example(
        summary="Staff login",
        description="Authenticate a staff account and receive an access token.",
        value={
            "username": "staff.reception",
            "password": "StrongPass123",
        },
    )
}


CREATE_MEMBER_REQUEST_EXAMPLES: dict[str, Example] = {
    "new_member": Example(
        summary="Create a new member",
        description="Register a new gym member with profile information.",
        value={
            "phone": "+84901234567",
            "full_name": "Nguyen Van A",
            "date_of_birth": "1998-05-20",
            "gender": "male",
            "avatar_url": "https://cdn.example.com/avatars/member-001.jpg",
            "note": "Prefers morning sessions.",
        },
    )
}


CREATE_CHECKIN_REQUEST_EXAMPLES: dict[str, Example] = {
    "member_visit": Example(
        summary="Record a check-in",
        description="Create a check-in entry for a member visiting the gym.",
        value={
            "member_id": "member_001",
            "checked_in_at": "2026-06-30T08:30:00Z",
            "note": "Morning cardio session.",
        },
    )
}


CREATE_USER_REQUEST_EXAMPLES: dict[str, Example] = {
    "staff_user": Example(
        summary="Create a staff user",
        description="Create a front-desk staff account managed by an administrator.",
        value={
            "username": "staff.frontdesk",
            "password": "StrongPass123",
            "full_name": "Tran Thi B",
            "role": "staff",
            "is_active": True,
        },
    )
}
