from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

if TYPE_CHECKING:
    from .doctor_profile import DoctorProfile


class Clinic(Base):
    """
    Represents a clinic organisation — the fundamental scoping unit in HelixOps.
    All appointments, staff, and patient records are scoped to a clinic.
    """

    __tablename__ = "clinics"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # URL-safe identifier, e.g. "city-health-clinic". Auto-generated from name.
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    doctor_profiles: Mapped[list[DoctorProfile]] = relationship(
        "DoctorProfile", back_populates="clinic", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Clinic id={self.id} name={self.name!r} slug={self.slug!r}>"
