from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import RefreshToken, User


class UserRepository:
    """
    Data access layer for User and RefreshToken tables.
    No business logic here — only DB queries.
    The service layer owns all decisions; this layer owns all SQL.
    """

    # User Queries

    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        password_hash: str,
        role: str,
        is_verified: bool = True,
        admin_clinic_id: uuid.UUID | None = None,
    ) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            role=role,
            is_verified=is_verified,
            is_active=True,
            admin_clinic_id=admin_clinic_id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def deactivate(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        await db.execute(
            update(User).where(User.id == user_id).values(is_active=False)
        )
        await db.commit()

    # Refresh Token Queries

    async def create_refresh_token(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    async def get_refresh_token_by_hash(
        self, db: AsyncSession, token_hash: str
    ) -> RefreshToken | None:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(
        self, db: AsyncSession, token_id: uuid.UUID
    ) -> None:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await db.commit()

    async def revoke_all_user_tokens(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """Revoke every active refresh token for a user (e.g., on password change)."""
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await db.commit()
