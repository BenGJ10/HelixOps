from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Request Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["patient"] = "patient"
    # Note: doctor, admin, super_admin accounts are provisioned by clinic admins / super admin.
    # Self-registration is restricted to patients only.

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Response Schemas
class UserPublic(BaseModel):
    """Public-safe user representation — never includes password_hash."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: str
    is_verified: bool
    is_active: bool
    admin_clinic_id: uuid.UUID | None = None
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

class MessageResponse(BaseModel):
    message: str
