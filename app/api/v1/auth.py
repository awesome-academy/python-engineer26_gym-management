from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import LOGIN_REQUEST_EXAMPLES, responses_for
from app.dependencies.auth import (
    get_current_user,
    get_refresh_token_from_cookie,
    get_token_from_bearer,
)
from app.dependencies.database import get_db
from app.models import User
from app.schemas import TokenResponse, LoginRequest
from app.services.auth import AuthService
from app.core import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Sign in",
    description="Authenticate a user and issue an access token with a refresh token cookie.",
    responses=responses_for(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def login(
    data: LoginRequest = Body(..., openapi_examples=LOGIN_REQUEST_EXAMPLES),
    session: AsyncSession = Depends(get_db),
) -> Response:
    tokens = await AuthService(session).login(data)

    token_response = TokenResponse(access_token=tokens["access_token"])
    response = JSONResponse(content=token_response.model_dump())

    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
    )

    return response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out",
    description="Invalidate the current access and refresh tokens and clear the refresh token cookie.",
    responses=responses_for(status.HTTP_401_UNAUTHORIZED),
)
async def logout(
    current_user: User = Depends(get_current_user),
    access_token: str = Depends(get_token_from_bearer),
    refresh_token: str = Depends(get_refresh_token_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> Response:
    await AuthService(session).logout(
        access_token=access_token,
        refresh_token=refresh_token,
    )

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
    )

    return response
