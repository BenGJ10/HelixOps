from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user, require_role
from ..db.session import get_db
from ..models.user import User
from ..repositories.clinic_repository import ClinicRepository
from ..schemas.auth import UserPublic
from ..schemas.clinic import (
    ClinicCreate,
    ClinicCreateResponse,
    ClinicPublic,
    ClinicWithAdmin,
    DoctorCreate,
    StaffMemberPublic,
)
from ..services.clinic_service import clinic_service, staff_service

router = APIRouter(prefix="/api/v1/clinics", tags=["Clinics"])
clinic_repo = ClinicRepository()


# Super Admin — Clinic Management

@router.post("", response_model=ClinicCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic(
    body: ClinicCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("super_admin")),
) -> ClinicCreateResponse:
    """
    [super_admin] Create a new clinic and provision its first admin account.
    The admin email + password are returned in the response (one-time).
    """
    clinic, admin = await clinic_service.create_clinic_with_admin(
        db=db,
        name=body.name,
        address=body.address,
        phone=body.phone,
        admin_email=body.admin_email,
        admin_password=body.admin_password,
    )
    return ClinicCreateResponse(
        clinic=ClinicPublic.model_validate(clinic),
        admin_email=admin.email,
    )


@router.get("", response_model=list[ClinicPublic])
async def list_clinics(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("super_admin")),
) -> list[ClinicPublic]:
    """[super_admin] List all clinics with pagination."""
    clinics = await clinic_service.list_clinics(db, skip=skip, limit=limit)
    return [ClinicPublic.model_validate(c) for c in clinics]


@router.get("/{clinic_id}", response_model=ClinicPublic)
async def get_clinic(
    clinic_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "admin")),
) -> ClinicPublic:
    """[super_admin, admin] Get a clinic's details. Admins can only view their own."""
    clinic = await clinic_service.get_clinic(db, clinic_id)

    # Admins may only inspect their own clinic
    if current_user.role == "admin" and current_user.admin_clinic_id != clinic_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied to this clinic.")

    return ClinicPublic.model_validate(clinic)


@router.delete("/{clinic_id}", response_model=ClinicPublic)
async def deactivate_clinic(
    clinic_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("super_admin")),
) -> ClinicPublic:
    """[super_admin] Deactivate a clinic (soft delete)."""
    clinic = await clinic_service.deactivate_clinic(db, clinic_id)
    return ClinicPublic.model_validate(clinic)


@router.patch("/{clinic_id}/activate", response_model=ClinicPublic)
async def activate_clinic(
    clinic_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("super_admin")),
) -> ClinicPublic:
    """[super_admin] Re-activate a previously deactivated clinic."""
    clinic = await clinic_service.activate_clinic(db, clinic_id)
    return ClinicPublic.model_validate(clinic)


@router.get("/stats/platform", response_model=dict)
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("super_admin")),
) -> dict:
    """[super_admin] Aggregate platform-wide stats for the overview dashboard."""
    return await clinic_repo.get_platform_stats(db)


# Admin — Staff Management

@router.post(
    "/{clinic_id}/staff",
    response_model=StaffMemberPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_doctor(
    clinic_id: uuid.UUID,
    body: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
) -> StaffMemberPublic:
    """
    [admin] Provision a new doctor account for this clinic.
    Doctors cannot self-register — they are created here by the clinic admin.
    """
    doctor_user, profile = await staff_service.create_doctor(
        db=db,
        admin=admin,
        clinic_id=clinic_id,
        email=body.email,
        password=body.password,
        specialty=body.specialty,
        license_number=body.license_number,
    )
    # Attach profile for serialisation
    doctor_user.doctor_profile = profile
    return StaffMemberPublic.model_validate(doctor_user)


@router.get("/{clinic_id}/staff", response_model=list[StaffMemberPublic])
async def list_staff(
    clinic_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
) -> list[StaffMemberPublic]:
    """[admin] List all doctors provisioned in this clinic."""
    profiles = await staff_service.list_staff(db, admin=admin, clinic_id=clinic_id)
    # Build StaffMemberPublic from the eagerly-loaded profile + user
    return [
        StaffMemberPublic(
            id=p.user.id,
            email=p.user.email,
            role=p.user.role,
            is_active=p.user.is_active,
            is_verified=p.user.is_verified,
            created_at=p.user.created_at,
            doctor_profile=p,
        )
        for p in profiles
    ]


@router.delete(
    "/{clinic_id}/staff/{user_id}",
    response_model=UserPublic,
)
async def deactivate_staff(
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
) -> UserPublic:
    """[admin] Deactivate a doctor account in this clinic."""
    doctor = await staff_service.deactivate_staff(
        db=db, admin=admin, clinic_id=clinic_id, user_id=user_id
    )
    return UserPublic.model_validate(doctor)
