"""Core domain enumerations. Pure — no I/O, no framework imports."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """User roles (BRD §7)."""

    DELIVERY_MANAGER = "delivery_manager"
    TECHNICAL_LEAD = "technical_lead"
    QA_LEAD = "qa_lead"
    DEVOPS_LEAD = "devops_lead"
    EXECUTIVE = "executive"
    ADMINISTRATOR = "administrator"


class Health(StrEnum):
    """Health status. ``UNKNOWN`` when minimum data is missing (BR-04)."""

    GREEN = "green"
    AMBER = "amber"
    RED = "red"
    UNKNOWN = "unknown"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class AgentKind(StrEnum):
    ORCHESTRATOR = "orchestrator"
    DELIVERY_ANALYST = "delivery_analyst"  # Phase 4 single-agent MVP
    BA = "ba_agent"
    DEVELOPMENT = "development_agent"
    QA = "qa_agent"
    DEVOPS = "devops_agent"
    PM = "pm_agent"


class HealthDimension(StrEnum):
    """Deterministic health dimensions (BRD §12)."""

    SCOPE = "scope"
    SCHEDULE = "schedule"
    QUALITY = "quality"
    ENGINEERING = "engineering"
    RELEASE_OPS = "release_ops"


class ConnectorType(StrEnum):
    WORK_ITEM = "work_item"
    REPOSITORY = "repository"
    TEST = "test"
    PIPELINE = "pipeline"
    DOCUMENT = "document"


class EvidenceSourceType(StrEnum):
    WORK_ITEM = "work_item"
    PULL_REQUEST = "pull_request"
    COMMIT = "commit"
    BUILD = "build"
    DEPLOYMENT = "deployment"
    TEST_RESULT = "test_result"
    DEFECT = "defect"
    DOCUMENT = "document"


class Sensitivity(StrEnum):
    """Data classification (Phase 0 decisions §5)."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ReportType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SPRINT = "sprint"
    RELEASE_READINESS = "release_readiness"
    EXECUTIVE = "executive"


class ReportStatus(StrEnum):
    DRAFT = "draft"
    EVALUATED = "evaluated"
    APPROVED = "approved"
    PUBLISHED = "published"
    BLOCKED = "blocked"  # failed a critical evaluation gate (BR-09, Phase 6)


class ApprovalStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class RunStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class FeedbackCategory(StrEnum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    IRRELEVANT = "irrelevant"
    MISSING_CONTEXT = "missing_context"


class EvaluatorType(StrEnum):
    GROUNDEDNESS = "groundedness"
    CITATION_VALIDITY = "citation_validity"
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"
    SCHEMA = "schema"
    POLICY = "policy"
    CONTRADICTION = "contradiction"
