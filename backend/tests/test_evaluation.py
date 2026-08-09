"""Unit tests for the AI quality gates and evaluators."""

from __future__ import annotations

import pytest
from app.application.evaluation import QualityGateEvaluator
from app.infrastructure.db.models import Report, Finding, Evidence, AgentRun
from app.domain.enums import ReportStatus, EvaluatorType, EvidenceSourceType


@pytest.mark.anyio
async def test_evaluation_success(session_factory, seeded):
    async with session_factory() as session:
        # 1. Create a dummy run and report
        run = AgentRun(user_id=seeded["pm_id"], project_id=seeded["project_id"], correlation_id="test", status="complete", request="Review")
        session.add(run)
        await session.flush()

        dummy_content = {
            "executive_summary": "ok",
            "progress_milestones": "ok",
            "scope_requirements": "ok",
            "development_health": "ok",
            "quality_readiness": "ok",
            "operations_environments": "ok",
            "scoring_engine": {}
        }
        report = Report(project_id=seeded["project_id"], run_id=run.id, period="sprint", report_type="daily", content=dummy_content, status="draft")
        session.add(report)
        await session.flush()

        # Add matching evidence and finding with correct citation
        evidence = Evidence(run_id=run.id, project_id=seeded["project_id"], source_type=EvidenceSourceType.WORK_ITEM, source_system="sys", source_record_id="WI-123", title="Valid title", retrieved_at=report.created_at)
        session.add(evidence)

        finding = Finding(run_id=run.id, agent="qa_agent", title="Test finding", severity="low", health="green", summary="summary", evidence_refs=[{"record_id": "WI-123"}])
        session.add(finding)
        await session.commit()

    async with session_factory() as session:
        evaluator = QualityGateEvaluator(session)
        evals = await evaluator.evaluate_report(run.id, report.id)

        assert len(evals) == 3
        # Groundedness must pass since WI-123 exists in evidence
        groundedness_eval = next(e for e in evals if e.evaluator_type == EvaluatorType.GROUNDEDNESS)
        assert groundedness_eval.result == "pass"
        assert groundedness_eval.score == 1.0

        # Reload report to check status
        reloaded_report = await session.get(Report, report.id)
        assert reloaded_report.status == ReportStatus.EVALUATED


@pytest.mark.anyio
async def test_evaluation_blocks_on_invalid_citation(session_factory, seeded):
    async with session_factory() as session:
        run = AgentRun(user_id=seeded["pm_id"], project_id=seeded["project_id"], correlation_id="test", status="complete", request="Review")
        session.add(run)
        await session.flush()

        dummy_content = {
            "executive_summary": "ok",
            "progress_milestones": "ok",
            "scope_requirements": "ok",
            "development_health": "ok",
            "quality_readiness": "ok",
            "operations_environments": "ok",
            "scoring_engine": {}
        }
        report = Report(project_id=seeded["project_id"], run_id=run.id, period="sprint", report_type="daily", content=dummy_content, status="draft")
        session.add(report)
        await session.flush()

        # Finding references "WI-999" which is NOT in evidence
        finding = Finding(run_id=run.id, agent="qa_agent", title="Test finding", severity="low", health="green", summary="summary", evidence_refs=[{"record_id": "WI-999"}])
        session.add(finding)
        await session.commit()

    async with session_factory() as session:
        evaluator = QualityGateEvaluator(session)
        evals = await evaluator.evaluate_report(run.id, report.id)

        groundedness_eval = next(e for e in evals if e.evaluator_type == EvaluatorType.GROUNDEDNESS)
        assert groundedness_eval.result == "fail"
        assert groundedness_eval.score == 0.0

        reloaded_report = await session.get(Report, report.id)
        assert reloaded_report.status == ReportStatus.BLOCKED
