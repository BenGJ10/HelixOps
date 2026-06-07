# Import models here so Alembic's autogenerate can find them via Base.metadata
# Order matters — Clinic must be imported before User (FK dependency)
from .clinic import Clinic
from .doctor_profile import DoctorProfile
from .user import RefreshToken, User

__all__ = ["Clinic", "DoctorProfile", "User", "RefreshToken"]
