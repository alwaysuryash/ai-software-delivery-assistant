"""Seed the database with the pilot project, users, access grants, and connector rows.

Run: ``python -m scripts.seed``  (after ``docker compose up -d`` and migrations/bootstrap).
Idempotent: safe to run repeatedly — existing rows (by natural key) are skipped.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.connectors.mock.sample_data import ITERATION
from app.domain.enums import ConnectorType, Role
from app.domain.rbac import Permission, permissions_for
from app.infrastructure.db.bootstrap import create_all
from app.infrastructure.db.models import Connector, Project, ProjectAccess, User
from app.infrastructure.db.session import get_engine, get_session_factory

SEED_USERS = [
    ("pm@acme.com", "Pat Morgan", Role.DELIVERY_MANAGER),
    ("techlead@acme.com", "Alex Rivera", Role.TECHNICAL_LEAD),
    ("qa@acme.com", "Quinn Lee", Role.QA_LEAD),
    ("devops@acme.com", "Devon Ops", Role.DEVOPS_LEAD),
    ("exec@acme.com", "Erin Chan", Role.EXECUTIVE),
    ("admin@acme.com", "Adah Min", Role.ADMINISTRATOR),
]

CONNECTORS = [
    (ConnectorType.WORK_ITEM, "Azure DevOps Boards", ["boards.read"]),
    (ConnectorType.REPOSITORY, "GitHub", ["repo.read", "pr.read"]),
    (ConnectorType.PIPELINE, "GitHub Actions / Azure Pipelines", ["builds.read", "deploys.read"]),
    (ConnectorType.TEST, "Azure Test Plans", ["tests.read", "defects.read"]),
    (ConnectorType.DOCUMENT, "Confluence", ["space.ALPHA.read"]),
]


async def _seed() -> None:
    await create_all(get_engine())
    factory = get_session_factory()
    async with factory() as session:
        # Users
        users: dict[str, User] = {}
        for email, name, role in SEED_USERS:
            existing = (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()
            if existing:
                users[email] = existing
                continue
            user = User(
                identity_provider_id=f"dev|{email}",
                email=email,
                display_name=name,
                role=role,
            )
            session.add(user)
            users[email] = user
        await session.flush()

        # Project Alpha
        project = (
            await session.execute(select(Project).where(Project.name == "Project Alpha"))
        ).scalar_one_or_none()
        if project is None:
            project = Project(
                name="Project Alpha",
                owner="pm@acme.com",
                status="active",
                sprint_calendar={"current_iteration": ITERATION, "release_target": "Friday"},
                health_config={},  # uses default health config unless overridden (Phase 3)
            )
            session.add(project)
            await session.flush()

        # Access grants — every seed user can access the pilot project
        for email, user in users.items():
            has = (
                await session.execute(
                    select(ProjectAccess).where(
                        ProjectAccess.user_id == user.id,
                        ProjectAccess.project_id == project.id,
                    )
                )
            ).scalar_one_or_none()
            if has is None:
                session.add(
                    ProjectAccess(
                        user_id=user.id,
                        project_id=project.id,
                        role=Role(user.role),
                        permissions=[p.value for p in permissions_for(Role(user.role))],
                    )
                )

        # Connector rows (read-only, write disabled by default)
        for ctype, name, scopes in CONNECTORS:
            exists = (
                await session.execute(
                    select(Connector).where(
                        Connector.project_id == project.id, Connector.type == ctype
                    )
                )
            ).scalar_one_or_none()
            if exists is None:
                session.add(
                    Connector(
                        project_id=project.id,
                        type=ctype,
                        name=name,
                        endpoint="mock://" + ctype.value,
                        credential_reference=f"kv://alpha/{ctype.value}",  # reference only
                        scopes=scopes,
                        status="enabled",
                        is_write_enabled=False,
                    )
                )

        await session.commit()
    print("Seed complete: users, Project Alpha, access grants, connectors.")  # noqa: T201


if __name__ == "__main__":
    asyncio.run(_seed())
