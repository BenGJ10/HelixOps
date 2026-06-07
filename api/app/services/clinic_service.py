from __future__ import annotations

import re
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import hash_password
from ..models.clinic import Clinic
from ..models.doctor_profile import DoctorProfile
from ..models.user import User
from ..repositories.clinic_repository import ClinicRepository
from ..repositories.user_repository import UserRepository

clinic_repo = ClinicRepository()
user_repo = UserRepository()


def _generate_slug(name: str) -> str:
    """Convert a clinic name to a URL-safe slug.
    
    Examples:
        "City Health Clinic" -> "city-health-clinic"
        "St. Mary's Hospital!!" -> "st-marys-hospital"
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)    # remove non-alphanumeric (except - and space)
    slug = re.sub(r"[\s_]+", "-", slug)     # spaces/underscores → hyphens
    slug = re.sub(r"-+", "-", slug)         # collapse multiple hyphens
    slug = slug.strip("-")
    return slug


class ClinicService:
    """
    Business logic for clinic lifecycle management.
    Super admin operations only — scope enforcement at router level via require_role.
    """

    async def create_clinic_with_admin(
        self,
        db: AsyncSession,
        name: str,
        address: str | None,
        phone: str | None,
        admin_email: str,
        admin_password: str,
    ) -> tuple[Clinic, User]:
        """
        Atomically:
        1. Generate a unique slug from the clinic name
        2. Create the clinic record
        3. Create the admin user account
        4. Link admin.admin_clinic_id → clinic.id

        Returns (clinic, admin_user).
        """
        
        # Slug uniqueness — append a counter if collision exists
        base_slug = _generate_slug(name)
        slug = base_slug
        counter = 1
        while await clinic_repo.get_clinic_by_slug(db, slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Check admin email isn't already taken
        existing = await user_repo.get_by_email(db, admin_email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with that admin email already exists.",
            )

        # Create clinic
        clinic = await clinic_repo.create_clinic(
            db=db, name=name, slug=slug, address=address, phone=phone
        )

        # Create admin user (no self-registration — provisioned here)
        admin_user = await user_repo.create_user(
            db=db,
            email=admin_email,
            password_hash=hash_password(admin_password),
            role="admin",
            is_verified=True,
            admin_clinic_id=clinic.id,
        )

        return clinic, admin_user

    async def get_clinic(self, db: AsyncSession, clinic_id: uuid.UUID) -> Clinic:
        clinic = await clinic_repo.get_clinic_by_id(db, clinic_id)
        if not clinic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinic not found.",
            )
        return clinic

    async def list_clinics(
        self, db: AsyncSession, skip: int = 0, limit: int = 50
    ) -> list[Clinic]:
        return await clinic_repo.list_clinics(db, skip=skip, limit=limit)

    async def deactivate_clinic(
        self, db: AsyncSession, clinic_id: uuid.UUID
    ) -> Clinic:
        clinic = await self.get_clinic(db, clinic_id)
        await clinic_repo.deactivate_clinic(db, clinic.id)
        clinic.is_active = False
        return clinic

    async def activate_clinic(
        self, db: AsyncSession, clinic_id: uuid.UUID
    ) -> Clinic:
        clinic = await clinic_repo.get_clinic_by_id(db, clinic_id)
        if not clinic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinic not found.",
            )
        result = await clinic_repo.activate_clinic(db, clinic.id)
        return result  # type: ignore[return-value]


class StaffService:
    """
    Business logic for clinic staff management.
    Admin operations — scope enforced by matching admin.admin_clinic_id to clinic_id.
    """

    async def _assert_clinic_scope(
        self, admin: User, clinic_id: uuid.UUID
    ) -> None:
        """Raise 403 if the admin is trying to manage a clinic they don't belong to."""
        if admin.admin_clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage staff within your own clinic.",
            )

    async def create_doctor(
        self,
        db: AsyncSession,
        admin: User,
        clinic_id: uuid.UUID,
        email: str,
        password: str,
        specialty: str | None,
        license_number: str | None,
    ) -> tuple[User, DoctorProfile]:
        """
        Provision a new doctor account for a clinic.
        Only a clinic admin can call this — and only for their own clinic.
        """
        await self._assert_clinic_scope(admin, clinic_id)

        # Ensure the clinic exists
        clinic = await clinic_repo.get_clinic_by_id(db, clinic_id)
        if not clinic or not clinic.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinic not found or inactive.",
            )

        # Check email uniqueness
        existing = await user_repo.get_by_email(db, email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        # Create doctor user
        doctor_user = await user_repo.create_user(
            db=db,
            email=email,
            password_hash=hash_password(password),
            role="doctor",
            is_verified=True,
        )

        # Create doctor profile linked to clinic
        profile = await clinic_repo.create_doctor_profile(
            db=db,
            user_id=doctor_user.id,
            clinic_id=clinic_id,
            specialty=specialty,
            license_number=license_number,
        )

        return doctor_user, profile

    async def list_staff(
        self, db: AsyncSession, admin: User, clinic_id: uuid.UUID
    ) -> list[DoctorProfile]:
        await self._assert_clinic_scope(admin, clinic_id)
        return await clinic_repo.list_clinic_staff(db, clinic_id)

    async def deactivate_staff(
        self,
        db: AsyncSession,
        admin: User,
        clinic_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> User:
        await self._assert_clinic_scope(admin, clinic_id)

        # Ensure doctor belongs to this clinic
        profile = await clinic_repo.get_doctor_profile_by_user_id(db, user_id)
        if not profile or profile.clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found in this clinic.",
            )

        await user_repo.deactivate(db, user_id)
        doctor = await user_repo.get_by_id(db, user_id)
        return doctor  # type: ignore[return-value]


clinic_service = ClinicService()
staff_service = StaffService()
