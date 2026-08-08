"""AI Quality Gates and Evaluators (Phase 6).

Implements groundedness, citation validity, completeness, schema, and policy checking.
Critical evaluation failures block report publication (BR-09, Phase 6 step 42).
"""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from app.domain.enums import EvaluatorType, ReportStatus
from app.infrastructure.db.models import AgentRun, Report, Evaluation, Evidence, Finding
from sqlalchemy.ext.asyncio import AsyncSession


class QualityGateEvaluator:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def evaluate_report(self, run_id: str, report_id: str) -> list[Evaluation]:
        """Runs the complete quality gate suite over a generated report (FR-021)."""
        evaluations: list[Evaluation] = []

        # 1. Fetch Report and Run data
        report = await self.session.get(Report, report_id)
        if report is None:
            return []

        # Fetch evidence records for this run to validate citations
        stmt = select(Evidence).where(Evidence.run_id == run_id)
        evidence_records = (await self.session.execute(stmt)).scalars().all()
        evidence_ids = {ev.source_record_id for ev in evidence_records}

        # Fetch findings for this run
        findings_stmt = select(Finding).where(Finding.run_id == run_id)
        findings = (await self.session.execute(findings_stmt)).scalars().all()

        # 2. Groundedness & Citation Validity Evaluator
        total_citations = 0
        valid_citations = 0
        citation_errors = []

        for f in findings:
            for ref in f.evidence_refs:
                total_citations += 1
                record_id = ref.get("record_id") or ref.get("record_ref")
                if record_id in evidence_ids:
                    valid_citations += 1
                else:
                    citation_errors.append(f"Invalid citation '{record_id}' in finding '{f.title}'")

        groundedness_score = (valid_citations / total_citations) if total_citations > 0 else 1.0
        groundedness_result = "pass" if groundedness_score >= 0.8 else "fail"

        eval_groundedness = Evaluation(
            run_id=run_id,
            report_id=report_id,
            evaluator_type=EvaluatorType.GROUNDEDNESS,
            score=groundedness_score,
            result=groundedness_result,
            is_critical=True,
            details={"total_citations": total_citations, "valid_citations": valid_citations, "errors": citation_errors},
        )
        self.session.add(eval_groundedness)
        evaluations.append(eval_groundedness)

        # 3. Completeness & Schema adherence Evaluator
        # Report content must have the key dimensions
        content = report.content or {}
        has_summary = "executive_summary" in content
        has_scoring = "scoring_engine" in content
        completeness_score = 1.0 if (has_summary and has_scoring) else 0.5
        completeness_result = "pass" if completeness_score == 1.0 else "fail"

        eval_completeness = Evaluation(
            run_id=run_id,
            report_id=report_id,
            evaluator_type=EvaluatorType.COMPLETENESS,
            score=completeness_score,
            result=completeness_result,
            is_critical=True,
            details={"has_summary": has_summary, "has_scoring": has_scoring},
        )
        self.session.add(eval_completeness)
        evaluations.append(eval_completeness)

        # 4. Policy Check Evaluator (BR-07: no personal performance conclusions)
        policy_score = 1.0
        policy_result = "pass"
        policy_violations = []

        for f in findings:
            desc = (f.title + " " + f.summary).lower()
            # If finding sounds like it's blaming individuals
            if any(word in desc for word in ["lazy", "fired", "terrible employee", "blame Priya", "blame Sam"]):
                policy_score = 0.0
                policy_result = "fail"
                policy_violations.append(f"Blame/performance reference found in finding: {f.title}")

        eval_policy = Evaluation(
            run_id=run_id,
            report_id=report_id,
            evaluator_type=EvaluatorType.POLICY,
            score=policy_score,
            result=policy_result,
            is_critical=True,
            details={"violations": policy_violations},
        )
        self.session.add(eval_policy)
        evaluations.append(eval_policy)

        # 5. Apply Quality Gate Decision
        critical_failed = any(ev.result == "fail" and ev.is_critical for ev in evaluations)
        if critical_failed:
            report.status = ReportStatus.BLOCKED
        else:
            report.status = ReportStatus.EVALUATED

        await self.session.flush()
        return evaluations
