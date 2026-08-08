"""Deterministic scoring engine implementing Project Health Model (BRD §12).

Calculates quantitative metrics, triggers, and health scores (0.0 to 100.0)
along with RAG statuses (green, amber, red, unknown).

Golden Rules:
- Health is UNKNOWN when minimum data is missing (BR-04).
- Deterministic engine calculates health, never the LLM alone.
"""

from __future__ import annotations

from typing import Any, TypedDict
from app.domain.enums import Health, Severity
from app.connectors.models import WorkItem, PullRequest, Build, Deployment, TestRun, Defect


class DimensionResult(TypedDict):
    health: Health
    score: float
    triggers_hit: list[str]
    details: dict[str, Any]


class HealthReportSummary(TypedDict):
    overall_health: Health
    overall_score: float
    dimensions: dict[str, DimensionResult]


def calculate_health(
    work_items: list[WorkItem] | None,
    pull_requests: list[PullRequest] | None,
    builds: list[Build] | None,
    deployments: list[Deployment] | None,
    test_runs: list[TestRun] | None,
    defects: list[Defect] | None,
) -> HealthReportSummary:
    """Calculate deterministic health scores and RAG statuses across 5 dimensions."""
    dimensions: dict[str, DimensionResult] = {}

    # 1. Scope Dimension (20% weight)
    if work_items is None:
        dimensions["scope"] = {
            "health": Health.UNKNOWN,
            "score": 0.0,
            "triggers_hit": ["Missing work items data"],
            "details": {},
        }
    else:
        triggers = []
        score = 100.0
        blocked_count = sum(1 for w in work_items if w.is_blocked)
        missing_ac_count = sum(1 for w in work_items if not w.acceptance_criteria_present)

        if missing_ac_count > 0:
            triggers.append(f"{missing_ac_count} work items missing acceptance criteria")
            score -= (missing_ac_count * 10)
        if blocked_count > 0:
            triggers.append(f"{blocked_count} blocked work items")
            score -= (blocked_count * 15)

        # Red trigger example: Critical requirement unresolved or unapproved scope expansion
        is_red = blocked_count > 0 or missing_ac_count > 2
        score = max(0.0, min(100.0, score))
        health = Health.RED if is_red else (Health.AMBER if score < 85 else Health.GREEN)

        dimensions["scope"] = {
            "health": health,
            "score": score,
            "triggers_hit": triggers,
            "details": {
                "total_items": len(work_items),
                "blocked_items": blocked_count,
                "missing_ac": missing_ac_count,
            },
        }

    # 2. Schedule Dimension (25% weight)
    if work_items is None:
        dimensions["schedule"] = {
            "health": Health.UNKNOWN,
            "score": 0.0,
            "triggers_hit": ["Missing work items data"],
            "details": {},
        }
    else:
        triggers = []
        score = 100.0
        overdue_count = 0
        total_points = sum(w.story_points or 0 for w in work_items)
        blocked_points = sum(w.story_points or 0 for w in work_items if w.is_blocked)

        for w in work_items:
            # Overdue check: state is active/blocked and has overdue date
            if w.state in ["active", "blocked", "new"] and w.due_date:
                overdue_count += 1

        if overdue_count > 0:
            triggers.append(f"{overdue_count} overdue active work items")
            score -= (overdue_count * 20)

        blocked_pct = (blocked_points / total_points * 100.0) if total_points > 0 else 0.0
        if blocked_pct > 0:
            score -= (blocked_pct * 0.5)

        # Red trigger: Critical milestone missed or blocked points > 30%
        is_red = overdue_count > 0 or blocked_pct > 30.0
        score = max(0.0, min(100.0, score))
        health = Health.RED if is_red else (Health.AMBER if score < 80 else Health.GREEN)

        dimensions["schedule"] = {
            "health": health,
            "score": score,
            "triggers_hit": triggers,
            "details": {
                "overdue_active_items": overdue_count,
                "blocked_points_pct": round(blocked_pct, 1),
                "total_points": total_points,
            },
        }

    # 3. Quality Dimension (25% weight)
    if test_runs is None or defects is None:
        dimensions["quality"] = {
            "health": Health.UNKNOWN,
            "score": 0.0,
            "triggers_hit": ["Missing testing or defects data"],
            "details": {},
        }
    else:
        triggers = []
        score = 100.0

        # Critical suite execution check
        critical_suites = [t for t in test_runs if t.is_critical_suite]
        unexecuted_critical_suites = []
        for cs in critical_suites:
            # If all blocked or none passed/failed, then unexecuted
            if cs.total > 0 and cs.blocked == cs.total:
                unexecuted_critical_suites.append(cs.suite)

        # Open release-blocking defects check
        open_blocking_defects = [
            d for d in defects if d.is_release_blocking and d.state not in ["closed", "resolved"]
        ]

        total_tests = sum(t.total for t in test_runs)
        passed_tests = sum(t.passed for t in test_runs)
        pass_rate = (passed_tests / total_tests * 100.0) if total_tests > 0 else 100.0

        if unexecuted_critical_suites:
            triggers.append(f"Critical suite not executed: {', '.join(unexecuted_critical_suites)}")
            score -= 40
        if open_blocking_defects:
            triggers.append(f"{len(open_blocking_defects)} open release-blocking defects")
            score -= 50
        if pass_rate < 95.0:
            score -= (100.0 - pass_rate) * 2

        is_red = len(open_blocking_defects) > 0 or len(unexecuted_critical_suites) > 0 or pass_rate < 80.0
        score = max(0.0, min(100.0, score))
        health = Health.RED if is_red else (Health.AMBER if score < 90 else Health.GREEN)

        dimensions["quality"] = {
            "health": health,
            "score": score,
            "triggers_hit": triggers,
            "details": {
                "pass_rate": round(pass_rate, 1),
                "open_release_blocking_defects": len(open_blocking_defects),
                "unexecuted_critical_suites": len(unexecuted_critical_suites),
            },
        }

    # 4. Engineering Dimension (15% weight)
    if pull_requests is None or builds is None:
        dimensions["engineering"] = {
            "health": Health.UNKNOWN,
            "score": 0.0,
            "triggers_hit": ["Missing engineering pipeline/PR data"],
            "details": {},
        }
    else:
        triggers = []
        score = 100.0

        # Main build status
        main_failed = any(
            b.branch == "main" and b.result == "failed" for b in builds
        )
        # Open PR age > 72 hours
        aged_prs = [pr for pr in pull_requests if pr.status == "open" and pr.age_hours > 72]

        if main_failed:
            triggers.append("Main build failed")
            score -= 40
        if aged_prs:
            triggers.append(f"{len(aged_prs)} open pull requests older than 72 hours")
            score -= (len(aged_prs) * 20)

        is_red = main_failed or len(aged_prs) > 1
        score = max(0.0, min(100.0, score))
        health = Health.RED if is_red else (Health.AMBER if score < 85 or aged_prs else Health.GREEN)

        dimensions["engineering"] = {
            "health": health,
            "score": score,
            "triggers_hit": triggers,
            "details": {
                "main_build_failed": main_failed,
                "aged_prs_count": len(aged_prs),
            },
        }

    # 5. Release / Operations Dimension (15% weight)
    if deployments is None:
        dimensions["operations"] = {
            "health": Health.UNKNOWN,
            "score": 0.0,
            "triggers_hit": ["Missing deployment data"],
            "details": {},
        }
    else:
        triggers = []
        score = 100.0

        # Check failed staging or production deployments that have not been successfully rolled back or validated
        failed_deploys = [
            d for d in deployments if d.result == "failed" and not d.rollback_validated
        ]

        if failed_deploys:
            triggers.append(f"{len(failed_deploys)} failed deployments without validated rollback")
            score -= 50

        is_red = len(failed_deploys) > 0
        score = max(0.0, min(100.0, score))
        health = Health.RED if is_red else (Health.AMBER if score < 90 else Health.GREEN)

        dimensions["operations"] = {
            "health": health,
            "score": score,
            "triggers_hit": triggers,
            "details": {
                "failed_unvalidated_deployments": len(failed_deploys),
            },
        }

    # Overall Health Calculation (Weighted Average or override if any dimension is RED)
    # Weights: Scope (20%), Schedule (25%), Quality (25%), Engineering (15%), Operations (15%)
    weights = {
        "scope": 0.20,
        "schedule": 0.25,
        "quality": 0.25,
        "engineering": 0.15,
        "operations": 0.15,
    }

    weighted_score = 0.0
    any_unknown = False
    any_red = False
    any_amber = False

    for dim, r in dimensions.items():
        if r["health"] == Health.UNKNOWN:
            any_unknown = True
        elif r["health"] == Health.RED:
            any_red = True
        elif r["health"] == Health.AMBER:
            any_amber = True

        weighted_score += r["score"] * weights[dim]

    if any_unknown:
        # If any of the required dimensions are missing completely, or overall cannot be computed safely
        overall_health = Health.UNKNOWN
    elif any_red:
        overall_health = Health.RED
    elif any_amber or weighted_score < 85:
        overall_health = Health.AMBER
    else:
        overall_health = Health.GREEN

    return {
        "overall_health": overall_health,
        "overall_score": round(weighted_score, 1),
        "dimensions": dimensions,
    }
