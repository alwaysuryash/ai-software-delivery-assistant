"""Mock connector implementations backed by deterministic sample data.

These satisfy Phase 1 step 20 (unblock front-end and agent development) and act as the reference
implementation of each connector port. Live connectors (Phase 2) implement the same interfaces.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.connectors.base import (
    ConnectorContext,
    DocumentConnector,
    PipelineConnector,
    RepositoryConnector,
    TestConnector,
    WorkItemConnector,
)
from app.connectors.mock import sample_data as sd
from app.connectors.models import (
    Build,
    Defect,
    Deployment,
    Document,
    PullRequest,
    TestRun,
    WorkItem,
)


def _now() -> datetime:
    return datetime.now(UTC)


class MockWorkItemConnector(WorkItemConnector):
    async def health_check(self, ctx: ConnectorContext) -> bool:
        return True

    async def list_work_items(
        self, ctx: ConnectorContext, *, iteration: str | None = None
    ) -> list[WorkItem]:
        items = sd.work_items(_now())
        if iteration:
            items = [i for i in items if i.iteration == iteration]
        return items


class MockRepositoryConnector(RepositoryConnector):
    async def health_check(self, ctx: ConnectorContext) -> bool:
        return True

    async def list_pull_requests(self, ctx: ConnectorContext) -> list[PullRequest]:
        return sd.pull_requests(_now())


class MockPipelineConnector(PipelineConnector):
    async def health_check(self, ctx: ConnectorContext) -> bool:
        return True

    async def list_builds(self, ctx: ConnectorContext) -> list[Build]:
        return sd.builds(_now())

    async def list_deployments(self, ctx: ConnectorContext) -> list[Deployment]:
        return sd.deployments(_now())


class MockTestConnector(TestConnector):
    async def health_check(self, ctx: ConnectorContext) -> bool:
        return True

    async def list_test_runs(self, ctx: ConnectorContext) -> list[TestRun]:
        return sd.test_runs(_now())

    async def list_defects(self, ctx: ConnectorContext) -> list[Defect]:
        return sd.defects(_now())


class MockDocumentConnector(DocumentConnector):
    async def health_check(self, ctx: ConnectorContext) -> bool:
        return True

    async def search_documents(self, ctx: ConnectorContext, query: str) -> list[Document]:
        docs = sd.documents(_now())
        q = query.lower().strip()
        if not q:
            return docs
        return [d for d in docs if q in d.excerpt.lower() or q in d.meta.title.lower()]
