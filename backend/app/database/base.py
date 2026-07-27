"""
Database Base — Declarative Base and health check helper.
"""

from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase
from app.database.session import engine


class Base(DeclarativeBase):
    """Base class for ORM models."""

    pass


async def check_db_connection() -> bool:
    """Verify database connection status."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
