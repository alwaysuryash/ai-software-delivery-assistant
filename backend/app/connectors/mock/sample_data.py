"""Deterministic sample data for the pilot project "Project Alpha".

Designed to exercise realistic delivery signals (BRD Appendix B scenario: is the team on track
for Friday's release?). It deliberately contains amber/red conditions: blocked work, an aged PR,
a failed main build, a critical test suite not executed, an open release-blocking defect, and a
production-like environment that is unavailable — so the health engine and agents have something
meaningful to reason about.

All records are generated relative to a supplied ``now`` for reproducibility (no hidden clock).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from app.connectors.models import (
    Build,
    Defect,
    Deployment,
    Document,
    PullRequest,
    SourceMeta,
    TestRun,
    WorkItem,
)
from app.domain.enums import EvidenceSourceType, Sensitivity

ITERATION = "Sprint 14"


def _hash(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:64]


def _meta(
    system: str,
    stype: EvidenceSourceType,
    rid: str,
    title: str,
    now: datetime,
    *,
    source_ts: datetime | None = None,
    uri: str | None = None,
    sensitivity: Sensitivity = Sensitivity.INTERNAL,
) -> SourceMeta:
    return SourceMeta(
        source_system=system,
        source_type=stype,
        record_id=rid,
        title=title,
        source_timestamp=source_ts or now,
        retrieved_at=now,
        access_uri=uri,
        sensitivity=sensitivity,
        content_hash=_hash(system, rid, title),
    )


def work_items(now: datetime) -> list[WorkItem]:
    S = EvidenceSourceType.WORK_ITEM
    return [
        WorkItem(
            meta=_meta("Azure DevOps Boards", S, "WI-1001", "Checkout flow — payment retry", now,
                       uri="https://dev.azure.com/alpha/_workitems/edit/1001"),
            work_item_type="story", state="active", assigned_to="Dana", story_points=5,
            iteration=ITERATION,
        ),
        WorkItem(
            meta=_meta("Azure DevOps Boards", S, "WI-1002", "Address validation service", now,
                       uri="https://dev.azure.com/alpha/_workitems/edit/1002"),
            work_item_type="story", state="blocked", assigned_to="Sam", story_points=8,
            is_blocked=True, iteration=ITERATION,
        ),
        WorkItem(
            meta=_meta("Azure DevOps Boards", S, "WI-1003", "Order confirmation email", now,
                       uri="https://dev.azure.com/alpha/_workitems/edit/1003"),
            work_item_type="story", state="resolved", assigned_to="Dana", story_points=3,
            iteration=ITERATION,
        ),
        WorkItem(
            meta=_meta("Azure DevOps Boards", S, "WI-1004", "Refund policy — acceptance criteria TBD",
                       now, uri="https://dev.azure.com/alpha/_workitems/edit/1004"),
            work_item_type="story", state="new", assigned_to=None, story_points=5,
            acceptance_criteria_present=False, iteration=ITERATION,
        ),
        WorkItem(
            meta=_meta("Azure DevOps Boards", S, "WI-1005", "Tax calc rounding", now,
                       uri="https://dev.azure.com/alpha/_workitems/edit/1005"),
            work_item_type="task", state="closed", assigned_to="Priya", story_points=2,
            iteration=ITERATION,
        ),
        WorkItem(
            meta=_meta("Azure DevOps Boards", S, "WI-1006", "Cart persistence", now,
                       source_ts=now - timedelta(days=3),
                       uri="https://dev.azure.com/alpha/_workitems/edit/1006"),
            work_item_type="story", state="active", assigned_to="Sam", story_points=5,
            due_date=now - timedelta(days=1), iteration=ITERATION,  # overdue
        ),
    ]


def pull_requests(now: datetime) -> list[PullRequest]:
    S = EvidenceSourceType.PULL_REQUEST
    return [
        PullRequest(
            meta=_meta("GitHub", S, "PR-311", "Payment retry logic", now,
                       uri="https://github.com/acme/alpha/pull/311"),
            status="open", author="Dana", created_at=now - timedelta(hours=96),
            reviewers=["Sam"], approvals=0, age_hours=96.0,  # aged PR, no approvals
        ),
        PullRequest(
            meta=_meta("GitHub", S, "PR-312", "Order email template", now,
                       uri="https://github.com/acme/alpha/pull/312"),
            status="merged", author="Dana", created_at=now - timedelta(hours=20),
            reviewers=["Priya"], approvals=2, age_hours=8.0,
        ),
    ]


def builds(now: datetime) -> list[Build]:
    S = EvidenceSourceType.BUILD
    return [
        Build(
            meta=_meta("GitHub Actions", S, "BUILD-889", "CI main", now,
                       source_ts=now - timedelta(hours=2),
                       uri="https://github.com/acme/alpha/actions/runs/889"),
            pipeline="ci-main", branch="main", result="failed",  # main build failed (red trigger)
            finished_at=now - timedelta(hours=2),
        ),
        Build(
            meta=_meta("GitHub Actions", S, "BUILD-890", "CI feature", now,
                       uri="https://github.com/acme/alpha/actions/runs/890"),
            pipeline="ci-feature", branch="feature/payment", result="succeeded",
            finished_at=now - timedelta(hours=1),
        ),
    ]


def deployments(now: datetime) -> list[Deployment]:
    S = EvidenceSourceType.DEPLOYMENT
    return [
        Deployment(
            meta=_meta("Azure Pipelines", S, "DEP-070", "Deploy to staging", now,
                       uri="https://dev.azure.com/alpha/_release?releaseId=70"),
            environment="staging", result="failed", rollback_validated=False,  # env unavailable
            finished_at=now - timedelta(hours=5),
        ),
    ]


def test_runs(now: datetime) -> list[TestRun]:
    S = EvidenceSourceType.TEST_RESULT
    return [
        TestRun(
            meta=_meta("Azure Test Plans", S, "TR-501", "Smoke suite", now,
                       uri="https://dev.azure.com/alpha/_testPlans/execute?runId=501"),
            suite="smoke", total=40, passed=39, failed=1, blocked=0, is_critical_suite=False,
        ),
        TestRun(
            meta=_meta("Azure Test Plans", S, "TR-502", "Critical regression suite", now,
                       uri="https://dev.azure.com/alpha/_testPlans/execute?runId=502"),
            suite="critical-regression", total=120, passed=0, failed=0, blocked=120,
            is_critical_suite=True,  # critical suite not executed (red trigger)
        ),
    ]


def defects(now: datetime) -> list[Defect]:
    S = EvidenceSourceType.DEFECT
    return [
        Defect(
            meta=_meta("Azure DevOps Boards", S, "BUG-77", "Payment double-charge on retry", now,
                       uri="https://dev.azure.com/alpha/_workitems/edit/77",
                       sensitivity=Sensitivity.CONFIDENTIAL),
            severity="critical", state="open", is_release_blocking=True, reopened_count=1,
        ),
        Defect(
            meta=_meta("Azure DevOps Boards", S, "BUG-78", "Email footer misaligned", now,
                       uri="https://dev.azure.com/alpha/_workitems/edit/78"),
            severity="low", state="open", is_release_blocking=False,
        ),
    ]


def documents(now: datetime) -> list[Document]:
    S = EvidenceSourceType.DOCUMENT
    return [
        Document(
            meta=_meta("Confluence", S, "DOC-Alpha-Plan", "Release Plan — Sprint 14", now,
                       uri="https://acme.atlassian.net/wiki/Alpha/ReleasePlan"),
            space="ALPHA", excerpt="Release targeted for Friday. Payment retry is a must-have.",
        ),
    ]
