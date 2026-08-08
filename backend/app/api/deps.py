"""FastAPI dependencies: DB session, current principal, and service factories."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.access import AccessService
from app.application.audit import AuditService
from app.core.security import AuthenticatedPrincipal, decode_access_token
from app.infrastructure.db.session import get_db_session

_bearer = HTTPBearer(auto_error=True)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> AuthenticatedPrincipal:
    return decode_access_token(credentials.credentials)


CurrentPrincipal = Annotated[AuthenticatedPrincipal, Depends(get_current_principal)]


def get_access_service(session: DbSession) -> AccessService:
    return AccessService(session)


def get_audit_service(session: DbSession) -> AuditService:
    return AuditService(session)


AccessDep = Annotated[AccessService, Depends(get_access_service)]
AuditDep = Annotated[AuditService, Depends(get_audit_service)]
