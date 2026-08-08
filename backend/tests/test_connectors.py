"""Tests for the mock connector framework and normalized evidence shape."""

from __future__ import annotations

from app.connectors.base import ConnectorContext
from app.connectors.registry import ConnectorRegistry
from app.domain.enums import ConnectorType


def _ctx() -> ConnectorContext:
    return ConnectorContext(project_id="p1", correlation_id="c1", allowed_scopes=frozenset())


async def test_work_item_connector_returns_normalized_records() -> None:
    connector = ConnectorRegistry().get(ConnectorType.WORK_ITEM)
    items = await connector.list_work_items(_ctx())  # type: ignore[attr-defined]
    assert items, "expected sample work items"
    # Every record carries provenance metadata (source id, retrieval timestamp).
    for wi in items:
        assert wi.meta.record_id
        assert wi.meta.retrieved_at is not None
        assert wi.meta.source_system == "Azure DevOps Boards"
    # Sample data deliberately includes a blocked item (amber/red signal).
    assert any(wi.is_blocked for wi in items)


async def test_test_connector_flags_unexecuted_critical_suite() -> None:
    connector = ConnectorRegistry().get(ConnectorType.TEST)
    runs = await connector.list_test_runs(_ctx())  # type: ignore[attr-defined]
    critical = [r for r in runs if r.is_critical_suite]
    assert critical, "expected a critical suite in sample data"
    # Critical regression suite is fully blocked / not executed (BRD §12 red trigger).
    assert critical[0].blocked == critical[0].total
    assert critical[0].passed == 0


async def test_pipeline_connector_reports_failed_main_build() -> None:
    connector = ConnectorRegistry().get(ConnectorType.PIPELINE)
    builds = await connector.list_builds(_ctx())  # type: ignore[attr-defined]
    main = [b for b in builds if b.branch == "main"]
    assert main and main[0].result == "failed"
