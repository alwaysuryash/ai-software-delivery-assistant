"""Unit tests for the deterministic health scoring engine."""

from __future__ import annotations

from datetime import datetime, UTC, timedelta
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
        retrieved_at=datetime.now(UTC),
    )


def test_calculate_health_all_green():
    work_items = [
        WorkItem(meta=_meta("sys", EvidenceSourceType.WORK_ITEM, "WI-1"), work_item_type="story", state="active")
    ]
    pull_requests = [
        PullRequest(meta=_meta("sys", EvidenceSourceType.PULL_REQUEST, "PR-1"), status="merged", author="Alice", created_at=datetime.now(UTC))
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


def test_calculate_health_custom_weights():
    # Only test_runs and defects provided, other dimensions are empty list (green with 100.0)
    work_items = []
    pull_requests = []
    builds = []
    deployments = []
    # Quality score is low because pass rate is 90% (lower than 95% threshold)
    test_runs = [
        TestRun(meta=_meta("sys", EvidenceSourceType.TEST_RESULT, "TR-1"), suite="smoke", total=10, passed=9, failed=1, blocked=0)
    ]
    defects = []

    # Defaults: Scope 20%, Schedule 25%, Quality 25%, Engineering 15%, Operations 15%
    # Quality has 90% pass rate. Penalty is (95 - 90) * 2 = 10 points -> Quality score = 90.0
    # Weighted score: 20%*100 + 25%*100 + 25%*90 + 15%*100 + 15%*100 = 20 + 25 + 22.5 + 15 + 15 = 97.5
    res_default = calculate_health(work_items, pull_requests, builds, deployments, test_runs, defects)
    assert res_default["overall_score"] == 97.5

    # If we assign 100% weight to Quality:
    health_config = {
        "weights": {
            "scope": 0.0,
            "schedule": 0.0,
            "quality": 1.0,
            "engineering": 0.0,
            "operations": 0.0
        }
    }
    res_custom = calculate_health(work_items, pull_requests, builds, deployments, test_runs, defects, health_config=health_config)
    assert res_custom["overall_score"] == 90.0


def test_calculate_health_custom_thresholds_and_overdue():
    current_time = datetime(2026, 7, 20, 12, 0, 0, tzinfo=UTC)

    # 1. Overdue Date calculation (timezone-safe)
    # Active items with past due date (overdue)
    wi_overdue_1 = WorkItem(
        meta=_meta("sys", EvidenceSourceType.WORK_ITEM, "WI-1"),
        work_item_type="story",
        state="active",
        due_date=datetime(2026, 7, 19, 12, 0, 0, tzinfo=UTC)
    )
    wi_overdue_2 = WorkItem(
        meta=_meta("sys", EvidenceSourceType.WORK_ITEM, "WI-2"),
        work_item_type="story",
        state="active",
        due_date=datetime(2026, 7, 18, 12, 0, 0, tzinfo=UTC)
    )
    # Active item with future due date (on track)
    wi_future = WorkItem(
        meta=_meta("sys", EvidenceSourceType.WORK_ITEM, "WI-3"),
        work_item_type="story",
        state="active",
        due_date=datetime(2026, 7, 21, 12, 0, 0, tzinfo=UTC)
    )

    # With default threshold: overdue_threshold = 0
    # Overdue count = 2. This hits the RED trigger (overdue_count > overdue_threshold)
    res_default = calculate_health([wi_overdue_1, wi_overdue_2, wi_future], [], [], [], [], [], current_time=current_time)
    assert res_default["dimensions"]["schedule"]["health"] == Health.RED

    # Custom Schedule threshold: overdue_threshold = 2
    # Overdue count of 2 is not > threshold (2), so it's not RED!
    health_config = {
        "schedule": {
            "overdue_threshold": 2
        }
    }
    res_custom = calculate_health([wi_overdue_1, wi_overdue_2, wi_future], [], [], [], [], [], health_config=health_config, current_time=current_time)
    assert res_custom["dimensions"]["schedule"]["health"] == Health.AMBER  # score reduced to 60.0, which is < 80 -> AMBER
