"""Domain and application exception hierarchy + FastAPI handlers.

Principle (BRD Appendix C): make every failure visible. Errors carry a stable ``code`` and a
safe, user-facing ``message`` — never leaking secrets or internal reasoning.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.correlation import get_correlation_id
from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base application error."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str = "An unexpected error occurred.") -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class AuthenticationError(AppError):
    status_code = 401
    code = "unauthenticated"


class AuthorizationError(AppError):
    """Raised when a user lacks project/connector access (BR-02)."""

    status_code = 403
    code = "forbidden"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class PolicyViolationError(AppError):
    """Raised when a business rule / policy gate blocks an action (e.g. BR-03)."""

    status_code = 409
    code = "policy_violation"


class ConnectorError(AppError):
    """Upstream connector failure — surfaced, never silently swallowed."""

    status_code = 502
    code = "connector_error"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("app_error", code=exc.code, status=exc.status_code, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "correlation_id": get_correlation_id(),
            }
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_error", path=request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred.",
                "correlation_id": get_correlation_id(),
            }
        },
    )
