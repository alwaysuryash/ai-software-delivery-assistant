"""Integration tests for the Multi-Agent Orchestrator."""

from __future__ import annotations

import pytest
from app.agents.orchestrator import MultiAgentOrchestrator
from app.domain.enums import RunStatus, Health


@pytest.mark.anyio
async def test_orchestrator_successful_run(session_factory, seeded):
    async with session_factory() as session:
        orchestrator = MultiAgentOrchestrator(session, "test-correlation-id")

        res = await orchestrator.execute_run(
            project_id=seeded["project_id"],
            user_id=seeded["pm_id"],
            request_text="Review Project Alpha for the current sprint."
        )

        assert res["status"] == "completed"
        assert "report_id" in res
        assert "scoring" in res
        assert res["scoring"]["overall_health"] == Health.RED  # Because Project Alpha has red signals!
        assert res["scoring"]["overall_score"] < 100.0
