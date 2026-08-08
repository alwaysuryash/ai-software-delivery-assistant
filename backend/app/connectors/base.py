"""Connector ports (interfaces).

Each connector is **replaceable** (BRD guardrail) and **permission-aware**. Concrete
implementations (mock or live) are resolved by the registry based on ``CONNECTOR_MODE``.
Read connectors only — write tools are handled by a separate, approval-gated path (Phase 7).

Reliability wrappers (timeout, retry, circuit breaker) are applied by the gateway in Phase 2;
the port itself stays minimal.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field

from app.connectors.models import (
    Build,
    Defect,
    Deployment,
    Document,
    PullRequest,
    TestRun,
    WorkItem,
)
from app.domain.enums import ConnectorType


@dataclass(frozen=True)
class ConnectorContext:
    """Scoped, authorized context for a connector call (BR-02).

    ``allowed_scopes`` and ``project_id`` are enforced by the gateway so a connector can only
    read data the user + project configuration authorize.
    """

    project_id: str
    correlation_id: str
    allowed_scopes: frozenset[str] = field(default_factory=frozenset)
    timeout_seconds: int = 20


class Connector(abc.ABC):
    """Base connector port."""

    type: ConnectorType

    @abc.abstractmethod
    async def health_check(self, ctx: ConnectorContext) -> bool:
        """Return True if the connector can reach its source (BRD Phase 2 step 24)."""


class WorkItemConnector(Connector):
    type = ConnectorType.WORK_ITEM

    @abc.abstractmethod
    async def list_work_items(self, ctx: ConnectorContext, *, iteration: str | None = None) -> list[WorkItem]: ...


class RepositoryConnector(Connector):
    type = ConnectorType.REPOSITORY

    @abc.abstractmethod
    async def list_pull_requests(self, ctx: ConnectorContext) -> list[PullRequest]: ...


class PipelineConnector(Connector):
    type = ConnectorType.PIPELINE

    @abc.abstractmethod
    async def list_builds(self, ctx: ConnectorContext) -> list[Build]: ...

    @abc.abstractmethod
    async def list_deployments(self, ctx: ConnectorContext) -> list[Deployment]: ...


class TestConnector(Connector):
    type = ConnectorType.TEST

    @abc.abstractmethod
    async def list_test_runs(self, ctx: ConnectorContext) -> list[TestRun]: ...

    @abc.abstractmethod
    async def list_defects(self, ctx: ConnectorContext) -> list[Defect]: ...


class DocumentConnector(Connector):
    type = ConnectorType.DOCUMENT

    @abc.abstractmethod
    async def search_documents(self, ctx: ConnectorContext, query: str) -> list[Document]: ...
