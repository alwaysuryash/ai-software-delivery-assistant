"""Test fixtures: in-memory async SQLite DB, seeded principals, and an ASGI client."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.enums import ConnectorType, Role
from app.domain.rbac import permissions_for
from app.infrastructure.db.base import Base
from app.infrastructure.db.models import Connector, Project, ProjectAccess, User
from app.infrastructure.db.session import get_db_session
from app.main import create_app


@pytest_asyncio.fixture
async def engine() -> AsyncIterator:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def seeded(session_factory) -> dict:
    """Seed users across all roles, Project Alpha, and access grants."""
    async with session_factory() as session:
        pm = User(
            identity_provider_id="dev|pm@acme.com",
            email="pm@acme.com",
            display_name="Pat Morgan",
            role=Role.DELIVERY_MANAGER,
        )
        techlead = User(
            identity_provider_id="dev|techlead@acme.com",
            email="techlead@acme.com",
            display_name="Alex Rivera",
            role=Role.TECHNICAL_LEAD,
        )
        exec_user = User(
            identity_provider_id="dev|exec@acme.com",
            email="exec@acme.com",
            display_name="Erin Chan",
            role=Role.EXECUTIVE,
        )
        outsider = User(
            identity_provider_id="dev|nobody@acme.com",
            email="nobody@acme.com",
            display_name="No Body",
            role=Role.DELIVERY_MANAGER,
        )
        session.add_all([pm, techlead, exec_user, outsider])
        await session.flush()

        project = Project(name="Project Alpha", owner="pm@acme.com", status="active")
        session.add(project)
        await session.flush()

        # Add access grants
        session.add(
            ProjectAccess(
                user_id=pm.id,
                project_id=project.id,
                role=Role.DELIVERY_MANAGER,
                permissions=[p.value for p in permissions_for(Role.DELIVERY_MANAGER)],
            )
        )
        session.add(
            ProjectAccess(
                user_id=techlead.id,
                project_id=project.id,
                role=Role.TECHNICAL_LEAD,
                permissions=[p.value for p in permissions_for(Role.TECHNICAL_LEAD)],
            )
        )
        session.add(
            ProjectAccess(
                user_id=exec_user.id,
                project_id=project.id,
                role=Role.EXECUTIVE,
                permissions=[p.value for p in permissions_for(Role.EXECUTIVE)],
            )
        )
        session.add(
            Connector(
                project_id=project.id,
                type=ConnectorType.WORK_ITEM,
                name="Azure DevOps Boards",
                endpoint="mock://work_item",
                credential_reference="kv://alpha/work_item",
                scopes=["boards.read"],
            )
        )
        await session.commit()
        return {"pm_id": pm.id, "outsider_id": outsider.id, "project_id": project.id}


@pytest_asyncio.fixture
async def client(engine, session_factory, seeded) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        c.seeded = seeded  # type: ignore[attr-defined]
        yield c


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
