"""Database engine and session configuration.

Uses SQLite via SQLAlchemy. The database file path can be overridden with the
``DATABASE_URL`` environment variable (handy for pointing tests at an
in-memory database).
"""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./address_book.db")

# `check_same_thread` is only needed for SQLite, which by default only
# allows the thread that created a connection to use it. FastAPI may serve
# a single request across different threads, so we relax that here.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
