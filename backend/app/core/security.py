"""Authentication primitives (FR-001).

Two auth providers behind one interface (NFR-12):
- ``dev``: local stub that issues signed JWTs for named seed users — enables offline development.
- ``entra_id``: validates Microsoft Entra ID (OIDC) tokens — wired in a later phase.

The application only ever depends on ``AuthenticatedPrincipal`` and ``decode_access_token``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.domain.enums import Role

_ALGORITHM = "HS256"
_ACCESS_TTL = timedelta(hours=8)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    user_id: str
    email: str
    display_name: str
    role: Role


def create_access_token(principal: AuthenticatedPrincipal, *, now: datetime | None = None) -> str:
    settings = get_settings()
    issued = now or datetime.now(UTC)
    claims = {
        "sub": principal.user_id,
        "email": principal.email,
        "name": principal.display_name,
        "role": principal.role.value,
        "iat": int(issued.timestamp()),
        "exp": int((issued + _ACCESS_TTL).timestamp()),
    }
    return jwt.encode(claims, settings.jwt_signing_secret, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> AuthenticatedPrincipal:
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.jwt_signing_secret, algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token.") from exc
    try:
        return AuthenticatedPrincipal(
            user_id=claims["sub"],
            email=claims["email"],
            display_name=claims.get("name", ""),
            role=Role(claims["role"]),
        )
    except (KeyError, ValueError) as exc:
        raise AuthenticationError("Malformed token claims.") from exc
