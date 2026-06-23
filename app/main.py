from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core import ErrorCode, settings, engine
from app.core.init_db import initialize_super_admin
from app.core.exceptions import AppException
from app.core.redis import init_redis, close_redis
from app.schemas import (
    ErrorResponse,
    FieldError,
    HealthResponse,
    ValidationErrorResponse,
)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up %s v%s", settings.APP_NAME, settings.APP_VERSION)
    await init_redis()
    try:
        await initialize_super_admin()
        yield
    finally:
        await close_redis()
        await engine.dispose()
        logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Any:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ).model_dump(exclude_none=True),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code_map = {
            status.HTTP_404_NOT_FOUND: ErrorCode.NOT_FOUND,
            status.HTTP_403_FORBIDDEN: ErrorCode.FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED: ErrorCode.UNAUTHORIZED,
        }
        error_code = code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code=error_code,
                message=str(exc.detail),
            ).model_dump(exclude_none=True),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            field_parts = [str(loc) for loc in error.get("loc", [])[1:]]
            field = ".".join(field_parts) if field_parts else "unknown"
            message = error.get("msg", "Invalid value")
            error_type = error.get("type", "validation_error")

            errors.append(
                FieldError(
                    field=field,
                    message=message,
                    code=error_type,
                )
            )

        response = ValidationErrorResponse(
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation error",
            errors=errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message="Internal server error",
            ).model_dump(exclude_none=True),
        )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    def health_check() -> HealthResponse:
        return HealthResponse(
            status="ok", app=settings.APP_NAME, version=settings.APP_VERSION
        )

    return app


app = create_app()
