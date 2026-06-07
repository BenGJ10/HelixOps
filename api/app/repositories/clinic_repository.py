from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.clinic import Clinic
from ..models.doctor_profile import DoctorProfile
from ..models.user import User


class ClinicRepository:
    """
    Data access layer for Clinic, DoctorProfile, and clinic-scoped User queries.
    """

    # Clinic Queries

    async def create_clinic(
        self,
        db: AsyncSession,
        name: str,
        slug: str,
        address: str | None,
        phone: str | None,
    ) -> Clinic:
        clinic = Clinic(name=name, slug=slug, address=address, phone=phone)
        db.add(clinic)
        await db.commit()
        await db.refresh(clinic)
        return clinic

    async def get_clinic_by_id(self, db: AsyncSession, clinic_id: uuid.UUID) -> Clinic | None:
        result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
        return result.scalar_one_or_none()

    async def get_clinic_by_slug(self, db: AsyncSession, slug: str) -> Clinic | None:
        result = await db.execute(select(Clinic).where(Clinic.slug == slug))
        return result.scalar_one_or_none()

    async def list_clinics(
        self, db: AsyncSession, skip: int = 0, limit: int = 50
    ) -> list[Clinic]:
        result = await db.execute(
            select(Clinic).order_by(Clinic.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def deactivate_clinic(self, db: AsyncSession, clinic_id: uuid.UUID) -> Clinic | None:
        await db.execute(
            update(Clinic).where(Clinic.id == clinic_id).values(is_active=False)
        )
        await db.commit()
        return await self.get_clinic_by_id(db, clinic_id)

    async def activate_clinic(self, db: AsyncSession, clinic_id: uuid.UUID) -> Clinic | None:
        await db.execute(
            update(Clinic).where(Clinic.id == clinic_id).values(is_active=True)
        )
        await db.commit()
        return await self.get_clinic_by_id(db, clinic_id)

    # DoctorProfile Queries

    async def create_doctor_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        clinic_id: uuid.UUID,
        specialty: str | None,
        license_number: str | None,
    ) -> DoctorProfile:
        profile = DoctorProfile(
            user_id=user_id,
            clinic_id=clinic_id,
            specialty=specialty,
            license_number=license_number,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    async def get_doctor_profile_by_user_id(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> DoctorProfile | None:
        result = await db.execute(
            select(DoctorProfile).where(DoctorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_clinic_staff(
        self, db: AsyncSession, clinic_id: uuid.UUID
    ) -> list[DoctorProfile]:
        """Return all DoctorProfiles in a given clinic, with their user eagerly loaded."""
        result = await db.execute(
            select(DoctorProfile)
            .where(DoctorProfile.clinic_id == clinic_id)
            .options(selectinload(DoctorProfile.user))
            .order_by(DoctorProfile.created_at.asc())
        )
        return list(result.scalars().all())

    # Admin / User Clinic Scope

    async def set_admin_clinic(
        self, db: AsyncSession, user_id: uuid.UUID, clinic_id: uuid.UUID
    ) -> None:
        """Assign a clinic to an admin user's admin_clinic_id field."""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(admin_clinic_id=clinic_id)
        )
        await db.commit()

    async def get_clinic_staff_count(
        self, db: AsyncSession, clinic_id: uuid.UUID
    ) -> int:
        result = await db.execute(
            select(DoctorProfile).where(DoctorProfile.clinic_id == clinic_id)
        )
        return len(result.scalars().all())

    async def get_platform_stats(self, db: AsyncSession) -> dict:
        """Aggregate counts for the super admin platform overview page."""
        from sqlalchemy import func as sqlfunc

        # Clinic counts
        clinic_result = await db.execute(
            select(Clinic.is_active, sqlfunc.count(Clinic.id)).group_by(Clinic.is_active)
        )
        clinic_rows = clinic_result.all()
        active_clinics = next((r[1] for r in clinic_rows if r[0] is True), 0)
        inactive_clinics = next((r[1] for r in clinic_rows if r[0] is False), 0)

        # User counts by role
        user_result = await db.execute(
            select(User.role, sqlfunc.count(User.id)).group_by(User.role)
        )
        role_counts = {row[0]: row[1] for row in user_result.all()}

        # Doctor profile count
        doctor_profile_count_result = await db.execute(
            select(sqlfunc.count(DoctorProfile.id))
        )
        total_doctor_profiles = doctor_profile_count_result.scalar_one() or 0

        return {
            "clinics": {
                "active": active_clinics,
                "inactive": inactive_clinics,
                "total": active_clinics + inactive_clinics,
            },
            "users": {
                "patients": role_counts.get("patient", 0),
                "doctors": role_counts.get("doctor", 0),
                "admins": role_counts.get("admin", 0),
                "super_admins": role_counts.get("super_admin", 0),
                "total": sum(role_counts.values()),
            },
            "doctor_profiles": total_doctor_profiles,
        }
