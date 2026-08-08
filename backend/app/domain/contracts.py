"""Domain contracts — the machine-readable schemas agents and connectors must honor.

The ``AgentResponse`` schema is the mandatory agent output contract (BRD §10.1). Every specialist
agent must return an object conforming to it. Evidence references are mandatory for material
findings (FR-011, BR-01).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AgentKind,
    AgentStatus,
    EvidenceSourceType,
    Health,
    Sensitivity,
    Severity,
)


class EvidenceRef(BaseModel):
    """A citation to a source record (FR-011). Every material claim must carry one."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(description="Human-readable source system, e.g. 'Test Management'")
    source_type: EvidenceSourceType
    record_id: str = Field(description="Source-system record identifier, e.g. 'TR-123'")
    retrieved_at: datetime = Field(description="ISO-8601 retrieval timestamp")
    access_uri: str | None = Field(default=None, description="Deep link to the source record")
    sensitivity: Sensitivity = Sensitivity.INTERNAL


class Finding(BaseModel):
    """A single evidence-backed finding produced by an agent."""

    title: str
    severity: Severity
    evidence: list[EvidenceRef] = Field(min_length=1, description="At least one citation required")
    impact: str
    recommendation: str
    owner: str | None = None
    due_date: date | None = None
    is_inference: bool = Field(
        default=False,
        description="If True, this is a labeled inference, not a directly-evidenced fact (BR-01)",
    )


class DataGap(BaseModel):
    """A visible, explicit missing/stale/inaccessible data condition (FR-012, BR-04)."""

    description: str
    affected_dimension: str | None = None
    source: str | None = None


class PolicyFlag(BaseModel):
    rule_id: str
    message: str


class AgentResponse(BaseModel):
    """Mandatory agent output contract (BRD §10.1)."""

    agent: AgentKind
    status: AgentStatus
    summary: str = Field(description="Concise evidence-based finding")
    health: Health
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[Finding] = Field(default_factory=list)
    data_gaps: list[DataGap] = Field(default_factory=list)
    policy_flags: list[PolicyFlag] = Field(default_factory=list)
