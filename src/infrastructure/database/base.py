"""SQLAlchemy declarative base and common utilities."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All database models should inherit from this class.
    This provides the declarative base for SQLAlchemy 2.0+.
    """

    pass
