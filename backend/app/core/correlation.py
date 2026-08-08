"""Correlation ID propagation (NFR-05: all interactions traceable by correlation ID).

A single correlation ID is generated per inbound request and stored in a context variable so
that logging, agent execution, tool calls, model calls, and audit events can all reference it.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

CORRELATION_HEADER = "X-Correlation-ID"


def new_correlation_id() -> str:
    return uuid.uuid4().hex


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def ensure_correlation_id(value: str | None) -> str:
    """Return the provided id or mint a new one, and bind it to the context."""
    cid = value or new_correlation_id()
    set_correlation_id(cid)
    return cid
