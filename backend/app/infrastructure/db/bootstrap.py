"""Schema bootstrap for local dev & tests.

Production uses Alembic migrations. For fast local iteration and the in-memory test database we
create the schema directly from the ORM metadata. Importing ``models`` registers all tables.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from app.infrastructure.db import models  # noqa: F401  (registers tables on Base.metadata)
from app.infrastructure.db.base import Base


async def create_all(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
