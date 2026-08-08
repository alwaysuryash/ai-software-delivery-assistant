"""Unit tests for the Human-in-the-Loop approvals and action executions."""

from __future__ import annotations

import pytest
from app.application.approval import ApprovalService
from app.domain.enums import ApprovalStatus
from app.core.errors import ValidationError


@pytest.mark.anyio
async def test_propose_and_approve_action(session_factory, seeded):
    async with session_factory() as session:
        service = ApprovalService(session)
        payload = {"action": "send_notification", "message": "hello"}

        action = await service.propose_action(
            project_id=seeded["project_id"],
            description="Notify team about release",
            priority="medium",
            payload=payload,
        )

        assert action.approval_status == ApprovalStatus.PENDING
        assert action.payload_hash is not None

        # Approve
        await service.approve_action(action.id, seeded["pm_id"])
        assert action.approval_status == ApprovalStatus.APPROVED


@pytest.mark.anyio
async def test_execute_action_hash_matching(session_factory, seeded):
    async with session_factory() as session:
        service = ApprovalService(session)
        payload = {"action": "send_notification", "message": "hello"}

        action = await service.propose_action(
            project_id=seeded["project_id"],
            description="Notify team",
            priority="medium",
            payload=payload,
        )
        await service.approve_action(action.id, seeded["pm_id"])

        # Execute with correct payload
        await service.execute_action(action.id, seeded["pm_id"], payload)
        assert action.approval_status == ApprovalStatus.EXECUTED


@pytest.mark.anyio
async def test_execute_action_rejects_payload_mismatch(session_factory, seeded):
    async with session_factory() as session:
        service = ApprovalService(session)
        payload = {"action": "send_notification", "message": "hello"}

        action = await service.propose_action(
            project_id=seeded["project_id"],
            description="Notify team",
            priority="medium",
            payload=payload,
        )
        await service.approve_action(action.id, seeded["pm_id"])

        # Execute with modified payload!
        modified_payload = {"action": "send_notification", "message": "hacked message"}
        with pytest.raises(ValidationError, match="Payload hash mismatch"):
            await service.execute_action(action.id, seeded["pm_id"], modified_payload)

        # Action should revert to PENDING
        assert action.approval_status == ApprovalStatus.PENDING
