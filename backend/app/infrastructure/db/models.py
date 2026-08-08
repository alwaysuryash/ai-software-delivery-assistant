"""ORM models implementing the BRD §15 Minimum Data Model.

Design notes:
- String primary keys are 32-char hex UUIDs (see ``UUIDPrimaryKeyMixin``).
- Enums are stored as their string values for portability and readability.
- JSON columns capture structured payloads (plans, findings, evidence lists) whose shape is
  validated by Pydantic contracts at the application boundary.
- ``AuditEvent`` is append-only by convention (no update/delete paths in the application layer).
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    ApprovalStatus,
    ConnectorType,
    EvaluatorType,
    EvidenceSourceType,
    FeedbackCategory,
    Health,
    ReportStatus,
    ReportType,
    Role,
    RunStatus,
    Sensitivity,
    Severity,
)
from app.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    identity_provider_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="active")

    project_access: Mapped[list[ProjectAccess]] = relationship(back_populates="user")


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), index=True)
    owner: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="active")
    sprint_calendar: Mapped[dict] = mapped_column(JSON, default=dict)
    health_config: Mapped[dict] = mapped_column(JSON, default=dict)

    access: Mapped[list[ProjectAccess]] = relationship(back_populates="project")
    connectors: Mapped[list[Connector]] = relationship(back_populates="project")


class ProjectAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_access"
    __table_args__ = (UniqueConstraint("user_id", "project_id", name="uq_user_project"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    role: Mapped[Role] = mapped_column(String(32))
    permissions: Mapped[list] = mapped_column(JSON, default=list)

    user: Mapped[User] = relationship(back_populates="project_access")
    project: Mapped[Project] = relationship(back_populates="access")


class Connector(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "connectors"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    type: Mapped[ConnectorType] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    endpoint: Mapped[str] = mapped_column(String(1024), default="")
    # A *reference* to a secret in the vault — never the secret itself (BRD §16, BR-08).
    credential_reference: Mapped[str] = mapped_column(String(512), default="")
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="enabled")
    is_write_enabled: Mapped[bool] = mapped_column(Boolean, default=False)  # off by default

    project: Mapped[Project] = relationship(back_populates="connectors")


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    request: Mapped[str] = mapped_column(Text)
    plan: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[RunStatus] = mapped_column(String(32), default=RunStatus.PLANNED)
    model_version: Mapped[str] = mapped_column(String(128), default="")
    prompt_version: Mapped[str] = mapped_column(String(128), default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ToolCall(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tool_calls"

    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    connector_id: Mapped[str | None] = mapped_column(ForeignKey("connectors.id"), nullable=True)
    operation: Mapped[str] = mapped_column(String(255))
    request_hash: Mapped[str] = mapped_column(String(64))
    response_reference: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(32), default="ok")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)


class Evidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evidence"

    run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id"), nullable=True, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    source_type: Mapped[EvidenceSourceType] = mapped_column(String(32))
    source_system: Mapped[str] = mapped_column(String(128))
    source_record_id: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(1024))
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    access_uri: Mapped[str] = mapped_column(String(1024), default="")
    sensitivity: Mapped[Sensitivity] = mapped_column(String(32), default=Sensitivity.INTERNAL)
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class Finding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "findings"

    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    agent: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(1024))
    severity: Mapped[Severity] = mapped_column(String(32))
    health: Mapped[Health] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    impact: Mapped[str] = mapped_column(Text, default="")
    recommendation: Mapped[str] = mapped_column(Text, default="")
    is_inference: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_refs: Mapped[list] = mapped_column(JSON, default=list)


class Risk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risks"

    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id"), index=True)
    probability: Mapped[str] = mapped_column(String(32))
    impact: Mapped[str] = mapped_column(String(32))
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mitigation: Mapped[str] = mapped_column(Text, default="")
    affected_milestone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open")


class Action(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "actions"

    source_finding_id: Mapped[str | None] = mapped_column(
        ForeignKey("findings.id"), nullable=True, index=True
    )
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[Severity] = mapped_column(String(32), default=Severity.MEDIUM)
    status: Mapped[str] = mapped_column(String(32), default="open")
    # Proposed write payload for a future approved action (Phase 7). Never executed without approval.
    proposed_write_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        String(32), default=ApprovalStatus.NOT_REQUIRED
    )


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id"), nullable=True)
    period: Mapped[str] = mapped_column(String(64))
    report_type: Mapped[ReportType] = mapped_column(String(32))
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    overall_health: Mapped[Health] = mapped_column(String(32), default=Health.UNKNOWN)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(String(32), default=ReportStatus.DRAFT)
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class Evaluation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluations"

    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("reports.id"), nullable=True)
    evaluator_type: Mapped[EvaluatorType] = mapped_column(String(32))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    result: Mapped[str] = mapped_column(String(32))  # pass | fail | warn
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class Feedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feedback"

    finding_id: Mapped[str | None] = mapped_column(ForeignKey("findings.id"), nullable=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("reports.id"), nullable=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[FeedbackCategory] = mapped_column(String(32))
    comments: Mapped[str] = mapped_column(Text, default="")


class AuditEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only audit trail (FR-021, NFR-05). Immutable by convention."""

    __tablename__ = "audit_events"

    actor: Mapped[str] = mapped_column(String(255), index=True)
    action: Mapped[str] = mapped_column(String(255), index=True)
    resource: Mapped[str] = mapped_column(String(512))
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    event_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
