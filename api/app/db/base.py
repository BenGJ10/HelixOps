from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared declarative base for all SQLAlchemy models.
    All models must inherit from this class so Alembic's
    autogenerate can detect them via Base.metadata.
    """
    pass
