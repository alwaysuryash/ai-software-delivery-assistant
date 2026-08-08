"""Normalized connector DTOs.

Every connector maps its source system's native records into these internal, source-agnostic
shapes (BRD Phase 2 step 22: "Normalize records into internal evidence schemas"). Each record
carries provenance metadata so it can be turned into an ``EvidenceRef`` (source id, deep link,
retrieval + source timestamps, sensitivity).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import EvidenceSourceType, Sensitivity


class SourceMeta(BaseModel):
    """Provenance carried by every normalized record."""

    source_system: str
    source_type: EvidenceSourceType
    record_id: str
    title: str
    source_timestamp: datetime | None = None
    retrieved_at: datetime
    access_uri: str | None = None
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    content_hash: str = ""


class WorkItem(BaseModel):
    meta: SourceMeta
    work_item_type: str  # story | task | bug | epic
    state: str  # new | active | resolved | closed | blocked
    assigned_to: str | None = None
    story_points: float | None = None
    is_blocked: bool = False
    iteration: str | None = None
    acceptance_criteria_present: bool = True
    due_date: datetime | None = None


class PullRequest(BaseModel):
    meta: SourceMeta
    status: str  # open | merged | closed
    author: str
    created_at: datetime
    reviewers: list[str] = Field(default_factory=list)
    approvals: int = 0
    age_hours: float = 0.0


class Build(BaseModel):
    meta: SourceMeta
    pipeline: str
    branch: str
    result: str  # succeeded | failed | canceled | partial
    finished_at: datetime | None = None


class Deployment(BaseModel):
    meta: SourceMeta
    environment: str
    result: str  # succeeded | failed | rolled_back
    rollback_validated: bool = False
    finished_at: datetime | None = None


class TestRun(BaseModel):
    meta: SourceMeta
    suite: str
    total: int
    passed: int
    failed: int
    blocked: int
    is_critical_suite: bool = False


class Defect(BaseModel):
    meta: SourceMeta
    severity: str  # low | medium | high | critical
    state: str  # open | in_progress | resolved | closed | reopened
    is_release_blocking: bool = False
    reopened_count: int = 0


class Document(BaseModel):
    meta: SourceMeta
    space: str
    excerpt: str
