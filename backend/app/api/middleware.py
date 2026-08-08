"""HTTP middleware: correlation IDs + structured request logging (NFR-05, NFR-11)."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.correlation import CORRELATION_HEADER, ensure_correlation_id
from app.core.logging import get_logger

logger = get_logger("http")


class CorrelationLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        cid = ensure_correlation_id(request.headers.get(CORRELATION_HEADER))
        start = time.perf_counter()
        logger.info("request_start", method=request.method, path=request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("request_error", method=request.method, path=request.url.path, ms=elapsed)
            raise
        elapsed = (time.perf_counter() - start) * 1000
        response.headers[CORRELATION_HEADER] = cid
        logger.info(
            "request_end",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=round(elapsed, 2),
        )
        return response
