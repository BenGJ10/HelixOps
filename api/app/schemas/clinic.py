from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Clinic Schemas

class ClinicCreate(BaseModel):
    """Request body for super_admin creating a new clinic + assigning its first admin."""
    name: str = Field(min_length=2, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=30)
    # The admin account created alongside the clinic
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)


class ClinicUpdate(BaseModel):
    """Request body for updating clinic details (partial update)."""
    name: str | None = Field(default=None, min_length=2, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=30)


class ClinicPublic(BaseModel):
    """Serialised clinic returned in API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    address: str | None
    phone: str | None
    is_active: bool
    created_at: datetime


class ClinicWithAdmin(BaseModel):
    """Clinic details plus the linked admin user's email."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    address: str | None
    phone: str | None
    is_active: bool
    created_at: datetime
    admin_email: str | None = None
    staff_count: int = 0


# Staff / Doctor Schemas

class DoctorCreate(BaseModel):
    """Request body for a clinic admin provisioning a new doctor account."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    specialty: str | None = Field(default=None, max_length=100)
    license_number: str | None = Field(default=None, max_length=50)


class DoctorUpdate(BaseModel):
    """Partial update for a doctor's profile fields."""
    specialty: str | None = Field(default=None, max_length=100)
    license_number: str | None = Field(default=None, max_length=50)


class DoctorProfilePublic(BaseModel):
    """Serialised doctor profile snippet."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    specialty: str | None
    license_number: str | None
    clinic_id: uuid.UUID | None


class StaffMemberPublic(BaseModel):
    """Full staff member — user identity + doctor profile."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    doctor_profile: DoctorProfilePublic | None = None


# Composite Responses

class ClinicCreateResponse(BaseModel):
    """Returned after creating a clinic — includes the newly created admin credentials."""
    clinic: ClinicPublic
    admin_email: str
    message: str = "Clinic created successfully. Admin account provisioned."
