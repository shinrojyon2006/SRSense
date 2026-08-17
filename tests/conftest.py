"""
Pytest global fixtures for SRSense AI testing.
"""

import pytest_asyncio
from app.database.session import engine


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_engine():
    """Ensure database connection pool is disposed cleanly between test functions."""
    yield
    await engine.dispose()
