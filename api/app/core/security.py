from __future__ import annotations

import uuid
import bcrypt
import hashlib
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from .config import settings

# Password Hashing using Bcrypt
def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt (auto-salted)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison of plain password against bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


# Access Token
def create_access_token(user_id: str, role: str, email: str) -> str:
    """
    Create a short-lived JWT access token (15 min).
    Sent in Authorization: Bearer <token> header.
    NOT stored in the database.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


# Refresh Token
def create_refresh_token(user_id: str) -> tuple[str, str]:
    """
    Create a long-lived JWT refresh token (7 days).

    Returns:
        (raw_token, token_hash)
        - raw_token: sent to the client as an httpOnly cookie
        - token_hash: stored in the database (SHA-256 of raw_token)

    Why hash? If the DB is ever breached, attackers get SHA-256 digests,
    not working tokens — same reason we hash passwords.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": str(uuid.uuid4()),  # unique token ID for identification
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    raw_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    token_hash = _hash_token(raw_token)
    return raw_token, token_hash


def hash_refresh_token(raw_token: str) -> str:
    """SHA-256 hash of a refresh token for DB lookup."""
    return _hash_token(raw_token)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# Token Decoding
def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    Raises:
        JWTError: if the token is invalid, expired, or tampered with.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
