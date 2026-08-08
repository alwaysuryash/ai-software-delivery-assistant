"""Project endpoints — authorized project listing & selection (FR-002, US-05).

A user only ever sees projects they have an explicit ``ProjectAccess`` grant for.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import AccessDep, CurrentPrincipal, DbSession
from app.api.schemas import ProjectSummary
from app.core.errors import AuthorizationError, NotFoundError
from app.domain.enums import Health
from app.domain.rbac import Permission
from app.infrastructure.db.models import Project, ProjectAccess

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
async def list_projects(principal: CurrentPrincipal, session: DbSession) -> list[ProjectSummary]:
    stmt = (
        select(Project)
        .join(ProjectAccess, ProjectAccess.project_id == Project.id)
        .where(ProjectAccess.user_id == principal.user_id)
        .order_by(Project.name)
    )
    projects = (await session.execute(stmt)).scalars().all()
    return [
        ProjectSummary(
            id=p.id,
            name=p.name,
            owner=p.owner,
            status=p.status,
            current_health=Health.UNKNOWN,  # computed by the scoring engine in Phase 3
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectSummary)
async def get_project(
    project_id: str,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> ProjectSummary:
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        # Uniform response — do not disclose project existence to unauthorized users (BR-02).
        raise NotFoundError("Project not found.") from None

    project = await session.get(Project, project_id)
    if project is None:
        raise NotFoundError("Project not found.")
    return ProjectSummary(
        id=project.id,
        name=project.name,
        owner=project.owner,
        status=project.status,
        current_health=Health.UNKNOWN,
    )
