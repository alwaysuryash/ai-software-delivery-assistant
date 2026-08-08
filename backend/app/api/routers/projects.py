"""Project endpoints — authorized project operations, assistant runs, and human-in-the-loop approvals (FR-002, US-05, US-06).
"""

from __future__ import annotations

from typing import Any
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import AccessDep, CurrentPrincipal, DbSession
from app.api.schemas import ProjectSummary
from app.core.errors import AuthorizationError, NotFoundError, ValidationError
from app.domain.enums import Health, ReportStatus, ApprovalStatus
from app.domain.rbac import Permission
from app.infrastructure.db.models import Project, ProjectAccess, Report, Action, Feedback, AuditEvent, Finding, Evaluation
from app.agents.orchestrator import MultiAgentOrchestrator
from app.application.evaluation import QualityGateEvaluator
from app.application.approval import ApprovalService

router = APIRouter(prefix="/projects", tags=["projects"])


class RunRequest(BaseModel):
    prompt: str


class FeedbackRequest(BaseModel):
    report_id: str | None = None
    finding_id: str | None = None
    rating: int | None = None
    category: str
    comments: str


class ActionExecuteRequest(BaseModel):
    payload: dict[str, Any]


@router.get("", response_model=list[ProjectSummary])
async def list_projects(principal: CurrentPrincipal, session: DbSession) -> list[ProjectSummary]:
    stmt = (
        select(Project)
        .join(ProjectAccess, ProjectAccess.project_id == Project.id)
        .where(ProjectAccess.user_id == principal.user_id)
        .order_by(Project.name)
    )
    projects = (await session.execute(stmt)).scalars().all()

    summaries = []
    for p in projects:
        # Get latest report overall health if exists, otherwise UNKNOWN
        report_stmt = select(Report).where(Report.project_id == p.id).order_by(Report.created_at.desc()).limit(1)
        latest_report = (await session.execute(report_stmt)).scalar_one_or_none()
        health = Health(latest_report.overall_health) if latest_report else Health.UNKNOWN

        summaries.append(
            ProjectSummary(
                id=p.id,
                name=p.name,
                owner=p.owner,
                status=p.status,
                current_health=health,
            )
        )
    return summaries


@router.get("/{project_id}", response_model=ProjectSummary)
async def get_project(
    project_id: str,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> ProjectSummary:
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        raise NotFoundError("Project not found.") from None

    project = await session.get(Project, project_id)
    if project is None:
        raise NotFoundError("Project not found.")

    report_stmt = select(Report).where(Report.project_id == project_id).order_by(Report.created_at.desc()).limit(1)
    latest_report = (await session.execute(report_stmt)).scalar_one_or_none()
    health = Health(latest_report.overall_health) if latest_report else Health.UNKNOWN

    return ProjectSummary(
        id=project.id,
        name=project.name,
        owner=project.owner,
        status=project.status,
        current_health=health,
    )


@router.post("/{project_id}/run")
async def run_assistant(
    project_id: str,
    req: RunRequest,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> dict[str, Any]:
    """Triggers multi-agent reasoning, deterministic scoring, and quality gates evaluation (Phase 4, 5, 6)."""
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        raise NotFoundError("Project not found.") from None

    # Run multi-agent intelligence orchestrator
    correlation_id = f"run-{datetime.utcnow().timestamp()}"
    orchestrator = MultiAgentOrchestrator(session, correlation_id)
    res = await orchestrator.execute_run(project_id, principal.user_id, req.prompt)

    # Automatically evaluate report quality gates
    evaluator = QualityGateEvaluator(session)
    evals = await evaluator.evaluate_report(res["run_id"], res["report_id"])

    # Reload report to return latest status
    report = await session.get(Report, res["report_id"])

    # Get evaluations as dicts
    eval_list = [
        {"evaluator_type": ev.evaluator_type, "score": ev.score, "result": ev.result, "details": ev.details}
        for ev in evals
    ]

    # Get findings list
    findings_stmt = select(Finding).where(Finding.run_id == res["run_id"])
    findings = (await session.execute(findings_stmt)).scalars().all()
    finding_list = [
        {
            "id": f.id, "agent": f.agent, "title": f.title, "severity": f.severity, "health": f.health,
            "summary": f.summary, "impact": f.impact, "recommendation": f.recommendation, "evidence_refs": f.evidence_refs
        }
        for f in findings
    ]

    return {
        "run_id": res["run_id"],
        "report": {
            "id": report.id,
            "overall_health": report.overall_health,
            "score": report.score,
            "status": report.status,
            "content": report.content,
            "findings": finding_list,
            "evaluations": eval_list,
        }
    }


@router.get("/{project_id}/reports")
async def list_reports(
    project_id: str,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> list[dict[str, Any]]:
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        raise NotFoundError("Project not found.") from None

    stmt = select(Report).where(Report.project_id == project_id).order_by(Report.created_at.desc())
    reports = (await session.execute(stmt)).scalars().all()

    res = []
    for r in reports:
        findings = []
        if r.run_id:
            findings_stmt = select(Finding).where(Finding.run_id == r.run_id)
            findings = (await session.execute(findings_stmt)).scalars().all()
        finding_list = [
            {
                "id": f.id, "agent": f.agent, "title": f.title, "severity": f.severity, "health": f.health,
                "summary": f.summary, "impact": f.impact, "recommendation": f.recommendation, "evidence_refs": f.evidence_refs
            }
            for f in findings
        ]

        evals_stmt = select(Evaluation).where(Evaluation.report_id == r.id)
        evals = (await session.execute(evals_stmt)).scalars().all()
        eval_list = [
            {"evaluator_type": ev.evaluator_type, "score": ev.score, "result": ev.result, "details": ev.details}
            for ev in evals
        ]

        res.append({
            "id": r.id,
            "period": r.period,
            "report_type": r.report_type,
            "overall_health": r.overall_health,
            "score": r.score,
            "status": r.status,
            "content": r.content,
            "findings": finding_list,
            "evaluations": eval_list,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return res


@router.post("/{project_id}/reports/{report_id}/approve")
async def approve_report(
    project_id: str,
    report_id: str,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> dict[str, Any]:
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        raise NotFoundError("Project not found.") from None

    report = await session.get(Report, report_id)
    if report is None or report.project_id != project_id:
        raise NotFoundError("Report not found.")

    if report.status == ReportStatus.BLOCKED:
        raise ValidationError("Cannot approve report. It has failed quality gate evaluators and is BLOCKED.")

    report.status = ReportStatus.APPROVED
    report.approved_by = principal.user_id

    # Log audit event
    session.add(
        AuditEvent(
            actor=principal.user_id,
            action="report_approved",
            resource=f"project/{project_id}/report/{report_id}",
            correlation_id="report-approval",
            event_metadata={"score": report.score},
        )
    )
    await session.commit()
    return {"id": report.id, "status": report.status}


@router.get("/{project_id}/actions")
async def list_actions(
    project_id: str,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> list[dict[str, Any]]:
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        raise NotFoundError("Project not found.") from None

    stmt = select(Action).where(Action.project_id == project_id).order_by(Action.created_at.desc())
    actions = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": a.id, "description": a.description, "owner": a.owner, "priority": a.priority,
            "status": a.status, "proposed_write_payload": a.proposed_write_payload, "payload_hash": a.payload_hash,
            "approval_status": a.approval_status, "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in actions
    ]


@router.post("/{project_id}/actions/{action_id}/approve")
async def approve_proposed_action(
    project_id: str,
    action_id: str,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> dict[str, Any]:
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        raise NotFoundError("Project not found.") from None

    approval_service = ApprovalService(session)
    action = await approval_service.approve_action(action_id, principal.user_id)
    await session.commit()
    return {"id": action.id, "approval_status": action.approval_status}


@router.post("/{project_id}/actions/{action_id}/execute")
async def execute_approved_action(
    project_id: str,
    action_id: str,
    req: ActionExecuteRequest,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> dict[str, Any]:
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        raise NotFoundError("Project not found.") from None

    approval_service = ApprovalService(session)
    action = await approval_service.execute_action(action_id, principal.user_id, req.payload)
    await session.commit()
    return {"id": action.id, "status": action.status, "approval_status": action.approval_status}


@router.post("/{project_id}/feedback")
async def submit_feedback(
    project_id: str,
    req: FeedbackRequest,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> dict[str, Any]:
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        raise NotFoundError("Project not found.") from None

    feedback = Feedback(
        finding_id=req.finding_id,
        report_id=req.report_id,
        user_id=principal.user_id,
        rating=req.rating,
        category=req.category,
        comments=req.comments,
    )
    session.add(feedback)
    await session.commit()
    return {"status": "feedback_submitted"}


@router.get("/{project_id}/audit")
async def list_audit_events(
    project_id: str,
    principal: CurrentPrincipal,
    session: DbSession,
    access: AccessDep,
) -> list[dict[str, Any]]:
    try:
        await access.require(principal, project_id, Permission.PROJECT_READ)
    except AuthorizationError:
        raise NotFoundError("Project not found.") from None

    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100)
    events = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": ev.id, "actor": ev.actor, "action": ev.action, "resource": ev.resource,
            "correlation_id": ev.correlation_id, "timestamp": ev.created_at.isoformat() if ev.created_at else None,
            "event_metadata": ev.event_metadata
        }
        for ev in events
    ]
