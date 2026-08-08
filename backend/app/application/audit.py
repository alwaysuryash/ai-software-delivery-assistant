"""Audit service (FR-021, NFR-05).

Writes immutable audit events for every sensitive interaction. Audit events are append-only;
the application exposes no update/delete path.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.correlation import get_correlation_id
from app.core.logging import get_logger
from app.infrastructure.db.models import AuditEvent

logger = get_logger(__name__)


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        actor: str,
        action: str,
        resource: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor=actor,
            action=action,
            resource=resource,
            correlation_id=get_correlation_id() or "",
            event_metadata=metadata or {},
        )
        self._session.add(event)
        await self._session.flush()
        logger.info("audit_event", actor=actor, action=action, resource=resource)
        return event
