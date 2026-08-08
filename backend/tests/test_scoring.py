"""Unit tests for the deterministic health scoring engine."""

from __future__ import annotations

from datetime import datetime, timedelta
import pytest

from app.domain.enums import Health, EvidenceSourceType, Sensitivity
from app.connectors.models import WorkItem, PullRequest, Build, Deployment, TestRun, Defect, SourceMeta
from app.domain.scoring import calculate_health


def _meta(sys: str, rtype: EvidenceSourceType, rid: str) -> SourceMeta:
    return SourceMeta(
        source_system=sys,
        source_type=rtype,
        record_id=rid,
        title="Test",
        retrieved_at=datetime.utcnow(),
    )


def test_calculate_health_all_green():
    work_items = [
        WorkItem(meta=_meta("sys", EvidenceSourceType.WORK_ITEM, "WI-1"), work_item_type="story", state="active")
    ]
    pull_requests = [
        PullRequest(meta=_meta("sys", EvidenceSourceType.PULL_REQUEST, "PR-1"), status="merged", author="Alice", created_at=datetime.utcnow())
    ]
    builds = [
        Build(meta=_meta("sys", EvidenceSourceType.BUILD, "B-1"), pipeline="ci", branch="main", result="succeeded")
    ]
    deployments = [
        Deployment(meta=_meta("sys", EvidenceSourceType.DEPLOYMENT, "D-1"), environment="staging", result="succeeded")
    ]
    test_runs = [
        TestRun(meta=_meta("sys", EvidenceSourceType.TEST_RESULT, "TR-1"), suite="smoke", total=10, passed=10, failed=0, blocked=0)
    ]
    defects = [
        Defect(meta=_meta("sys", EvidenceSourceType.DEFECT, "BUG-1"), severity="low", state="closed")
    ]

    res = calculate_health(work_items, pull_requests, builds, deployments, test_runs, defects)
    assert res["overall_health"] == Health.GREEN
    assert res["overall_score"] == 100.0


def test_calculate_health_red_trigger_quality():
    work_items = []
    pull_requests = []
    builds = []
    deployments = []
    test_runs = [
        # Critical regression suite not executed
        TestRun(meta=_meta("sys", EvidenceSourceType.TEST_RESULT, "TR-2"), suite="critical", total=100, passed=0, failed=0, blocked=100, is_critical_suite=True)
    ]
    defects = []

    res = calculate_health(work_items, pull_requests, builds, deployments, test_runs, defects)
    assert res["dimensions"]["quality"]["health"] == Health.RED
    assert res["overall_health"] == Health.RED


def test_calculate_health_unknown_on_missing_data():
    res = calculate_health(None, [], [], [], [], [])
    assert res["overall_health"] == Health.UNKNOWN
    assert res["dimensions"]["scope"]["health"] == Health.UNKNOWN
