from fastapi import status


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details if details is not None else {}
        super().__init__(self.message)


class ValidationException(AppException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            code="validation_error",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(
            code=code or "unauthorized",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(
            code=code or "forbidden",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundException(AppException):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(
            code=code or "not_found",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictException(AppException):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(
            code=code or "conflict",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class InternalServerException(AppException):
    def __init__(self, message: str = "Internal server error", code: str | None = None):
        super().__init__(
            code=code or "internal_server_error",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
