"""Authentication endpoints.

- ``POST /auth/dev-login`` issues a token for a seed user. **Only enabled outside production**
  and only when ``AUTH_PROVIDER=dev`` — this is the offline development path (FR-001 stub).
- ``GET /auth/me`` returns the current principal.

Entra ID (OIDC) token exchange is added in a later phase behind the same token abstraction.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentPrincipal, DbSession
from app.api.schemas import DevLoginRequest, TokenResponse, UserResponse
from app.core.config import AppEnv, AuthProviderKind, get_settings
from app.core.errors import AuthenticationError
from app.core.security import AuthenticatedPrincipal, create_access_token
from app.domain.enums import Role
from app.infrastructure.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(payload: DevLoginRequest, session: DbSession) -> TokenResponse:
    settings = get_settings()
    if settings.app_env == AppEnv.PROD or settings.auth_provider != AuthProviderKind.DEV:
        raise AuthenticationError("Dev login is disabled in this environment.")

    result = await session.execute(select(User).where(User.email == str(payload.email)))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationError("Unknown user.")

    principal = AuthenticatedPrincipal(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=Role(user.role),
    )
    return TokenResponse(access_token=create_access_token(principal))


@router.get("/me", response_model=UserResponse)
async def me(principal: CurrentPrincipal) -> UserResponse:
    return UserResponse(
        id=principal.user_id,
        email=principal.email,
        display_name=principal.display_name,
        role=principal.role,
    )
