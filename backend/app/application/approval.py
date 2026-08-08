"""Human-in-the-Loop Approval and Write Actions (Phase 7).

Ensures no write action occurs without explicit human approval bound to
the exact payload hash (BR-03, FR-017).
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, UTC
from typing import Any

from app.domain.enums import ApprovalStatus
from app.infrastructure.db.models import Action, AuditEvent
from app.core.errors import AuthorizationError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class ApprovalService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _compute_hash(self, payload: dict[str, Any]) -> str:
        """Deterministically hashes the payload dictionary (BR-03)."""
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()[:64]

    async def propose_action(
        self, project_id: str, description: str, priority: str, payload: dict[str, Any]
    ) -> Action:
        """Create a proposed write action with a strict payload hash constraint."""
        payload_hash = self._compute_hash(payload)
        action = Action(
            project_id=project_id,
            description=description,
            priority=priority,
            status="open",
            proposed_write_payload=payload,
            payload_hash=payload_hash,
            approval_status=ApprovalStatus.PENDING,
        )
        self.session.add(action)
        await self.session.flush()
        return action

    async def approve_action(self, action_id: str, user_id: str) -> Action:
        """Mark a proposed action as approved by a human (PM/Approver)."""
        action = await self.session.get(Action, action_id)
        if action is None:
            raise ValidationError("Action not found.")

        action.approval_status = ApprovalStatus.APPROVED

        # Log audit event
        self.session.add(
            AuditEvent(
                actor=user_id,
                action="action_approved",
                resource=f"action/{action_id}",
                correlation_id="approval-flow",
                event_metadata={"payload_hash": action.payload_hash},
            )
        )
        await self.session.flush()
        return action

    async def execute_action(self, action_id: str, user_id: str, current_payload: dict[str, Any]) -> Action:
        """Execute the action, verifying that current_payload matches the approved hash."""
        action = await self.session.get(Action, action_id)
        if action is None:
            raise ValidationError("Action not found.")

        if action.approval_status != ApprovalStatus.APPROVED:
            raise ValidationError("Action cannot be executed because it is not approved.")

        # Bind approval to exact payload hash (BR-03, Phase 7 step 47)
        current_hash = self._compute_hash(current_payload)
        if current_hash != action.payload_hash:
            # Payload was modified! Reject and force reapproval.
            action.approval_status = ApprovalStatus.PENDING
            self.session.add(
                AuditEvent(
                    actor=user_id,
                    action="action_execution_rejected_payload_mismatch",
                    resource=f"action/{action_id}",
                    correlation_id="execution-flow",
                    event_metadata={"expected_hash": action.payload_hash, "received_hash": current_hash},
                )
            )
            await self.session.flush()
            raise ValidationError("Payload hash mismatch! The proposed action payload has changed and requires reapproval.")

        # Safe to execute!
        action.approval_status = ApprovalStatus.EXECUTED
        action.status = "closed"

        self.session.add(
            AuditEvent(
                actor=user_id,
                action="action_executed",
                resource=f"action/{action_id}",
                correlation_id="execution-flow",
                event_metadata={"payload": current_payload},
            )
        )
        await self.session.flush()
        return action
