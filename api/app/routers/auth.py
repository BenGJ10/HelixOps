from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.user import User
from ..schemas.auth import LoginRequest, MessageResponse, RegisterRequest, TokenResponse, UserPublic
from ..services.auth_service import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Cookie name and path constants
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth/refresh"
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    """Helper — sets the httpOnly refresh token cookie with correct security flags."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        httponly=True,                                      # JS cannot read it
        max_age=REFRESH_COOKIE_MAX_AGE,
        samesite="lax",                                     # CSRF protection
        secure=settings.ENVIRONMENT != "development",       # HTTPS-only in prod
        path=REFRESH_COOKIE_PATH,                           # Scoped to refresh endpoint only
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Helper — removes the refresh token cookie."""
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Register a new user account.
    Part A: auto-verified. Part B: will send verification email.
    """
    user = await auth_service.register(db, body.email, body.password, body.role)

    # Log the user in immediately after registration
    access_token, raw_refresh, _ = await auth_service.login(db, body.email, body.password)
    _set_refresh_cookie(response, raw_refresh)

    return TokenResponse(
        access_token=access_token,
        user=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email + password.
    Returns access token in body, refresh token as httpOnly cookie.
    """
    access_token, raw_refresh, user = await auth_service.login(db, body.email, body.password)
    _set_refresh_cookie(response, raw_refresh)

    return TokenResponse(
        access_token=access_token,
        user=UserPublic.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Rotate tokens using the httpOnly refresh token cookie.
    Issues a new access token and a new refresh token (rotation).
    """
    raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found. Please log in.",
        )

    access_token, new_raw_refresh, user = await auth_service.refresh_tokens(db, raw_refresh)
    _set_refresh_cookie(response, new_raw_refresh)

    return TokenResponse(
        access_token=access_token,
        user=UserPublic.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Revoke the current refresh token in the DB and clear the cookie.
    Access token expires naturally (15 min). Client should discard it from memory.
    """
    raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    await auth_service.logout(db, raw_refresh)
    _clear_refresh_cookie(response)

    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserPublic)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserPublic:
    """Returns the currently authenticated user's profile."""
    return UserPublic.model_validate(current_user)
