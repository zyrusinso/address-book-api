"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Address(Base):
    """A single address book entry, including its geographic coordinates."""

    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    street: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(120), nullable=False)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
