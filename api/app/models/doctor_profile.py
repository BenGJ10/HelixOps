from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

if TYPE_CHECKING:
    from .clinic import Clinic
    from .user import User


class DoctorProfile(Base):
    """
    Side table that extends `users` for doctor-specific clinical attributes.

    Design rationale:
    - Keeps the `users` table lean and role-agnostic (it's the identity record).
    - Doctor-specific fields (specialty, license) live here and are only
      populated for users with role='doctor'.
    - Follows the same pattern we'll use for PatientProfile in Phase 3.
    """

    __tablename__ = "doctor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # One-to-one with users — unique ensures no duplicate profiles
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # Nullable — SET NULL if clinic is deleted (doctor profile survives)
    clinic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    specialty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships — imported only under TYPE_CHECKING to avoid circular imports
    user: Mapped[User] = relationship("User", back_populates="doctor_profile")
    clinic: Mapped[Optional[Clinic]] = relationship("Clinic", back_populates="doctor_profiles")

    def __repr__(self) -> str:
        return f"<DoctorProfile id={self.id} user_id={self.user_id} clinic_id={self.clinic_id}>"
