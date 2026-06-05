from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from ..models.user import User
from ..repositories.user_repository import UserRepository

user_repo = UserRepository()


class AuthService:
    """
    All authentication business logic lives here.
    Routers call this service — never query the DB directly from a router.
    """

    async def register(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        role: str,
    ) -> User:
        """
        Register a new user.
        Part A: users are auto-verified (is_verified=True).
        Part B: will send verification email and set is_verified=False.
        """
        existing = await user_repo.get_by_email(db, email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        user = await user_repo.create_user(
            db=db,
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_verified=True,  # Part A: auto-verified
        )
        return user

    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> tuple[str, str, User]:
        """
        Authenticate user credentials and issue a token pair.

        Returns:
            (access_token, raw_refresh_token, user)
        """
        user = await user_repo.get_by_email(db, email)

        # Use the same error for wrong email OR wrong password
        # — never reveal which one is incorrect (enumeration protection)
        if not user or not verify_password(password, user.password_hash or ""):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated.",
            )

        access_token = create_access_token(str(user.id), user.role, user.email)
        raw_refresh, token_hash = create_refresh_token(str(user.id))
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        await user_repo.create_refresh_token(
            db=db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return access_token, raw_refresh, user

    async def refresh_tokens(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
    ) -> tuple[str, str, User]:
        """
        Rotate the refresh token.

        Flow:
          1. Decode JWT — reject if invalid/expired
          2. Look up hash in DB — reject if not found or already revoked
          3. Revoke the old token
          4. Issue a new access + refresh token pair
          5. Store new token hash in DB

        Why rotation? If a stolen refresh token is used, the legitimate
        user's next refresh will find their token already revoked → both
        tokens are then invalidated, bounding the attack window.
        """
        try:
            payload = decode_token(raw_refresh_token)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong token type.",
            )

        token_hash = hash_refresh_token(raw_refresh_token)
        db_token = await user_repo.get_refresh_token_by_hash(db, token_hash)

        if not db_token or db_token.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or has been revoked.",
            )

        if db_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again.",
            )

        user = await user_repo.get_by_id(db, db_token.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive.",
            )

        # Revoke old token
        await user_repo.revoke_refresh_token(db, db_token.id)

        # Issue new token pair
        access_token = create_access_token(str(user.id), user.role, user.email)
        raw_refresh, new_hash = create_refresh_token(str(user.id))
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        await user_repo.create_refresh_token(
            db=db,
            user_id=user.id,
            token_hash=new_hash,
            expires_at=expires_at,
        )

        return access_token, raw_refresh, user

    async def logout(
        self,
        db: AsyncSession,
        raw_refresh_token: str | None,
    ) -> None:
        """
        Revoke the refresh token in the DB.
        No Redis needed — the token entry is simply marked revoked.
        Client is responsible for discarding the access token from memory.
        """
        if not raw_refresh_token:
            return

        token_hash = hash_refresh_token(raw_refresh_token)
        db_token = await user_repo.get_refresh_token_by_hash(db, token_hash)

        if db_token and db_token.revoked_at is None:
            await user_repo.revoke_refresh_token(db, db_token.id)


auth_service = AuthService()
