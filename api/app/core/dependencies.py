from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Coroutine

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from .security import decode_token
from ..db.session import get_db
from ..models.user import User
from ..repositories.user_repository import UserRepository

security = HTTPBearer(auto_error=True)
_user_repo = UserRepository()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency — extracts and validates the JWT access token.
    Inject this into any route that requires authentication.

    Usage:
        @router.get("/me")
        async def me(user: User = Depends(get_current_user)):
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong token type. Use access token.",
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token — missing subject.",
        )

    user = await _user_repo.get_by_id(db, uuid.UUID(user_id_str))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    return user


def require_role(*roles: str) -> Callable[..., Coroutine]:
    """
    Dependency factory for role-based access control.

    Usage:
        # Doctor or Admin only
        @router.get("/appointments")
        async def appointments(user: User = Depends(require_role("doctor", "admin"))):

        # Super admin only
        @router.post("/clinics")
        async def create_clinic(user: User = Depends(require_role("super_admin"))):
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(roles)}.",
            )
        return current_user

    return role_checker
