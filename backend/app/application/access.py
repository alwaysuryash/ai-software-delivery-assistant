"""Project access & authorization service (FR-002, BR-02, US-05).

Enforces that a user without project access cannot query, retrieve, infer, or view a project's
data. Capability checks combine the user's role permissions (RBAC matrix) with an explicit
``ProjectAccess`` grant.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthorizationError
from app.core.security import AuthenticatedPrincipal
from app.domain.rbac import Permission, role_has_permission
from app.infrastructure.db.models import ProjectAccess


class AccessService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_project_access(self, user_id: str, project_id: str) -> bool:
        result = await self._session.execute(
            select(ProjectAccess).where(
                ProjectAccess.user_id == user_id,
                ProjectAccess.project_id == project_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def require(
        self,
        principal: AuthenticatedPrincipal,
        project_id: str,
        permission: Permission,
    ) -> None:
        """Raise ``AuthorizationError`` unless the principal may exercise ``permission`` on the project."""
        if not role_has_permission(principal.role, permission):
            raise AuthorizationError("Your role does not permit this action.")
        if not await self.has_project_access(principal.user_id, project_id):
            # Do not disclose whether the project exists (BR-02 / US-05).
            raise AuthorizationError("You do not have access to this project.")
