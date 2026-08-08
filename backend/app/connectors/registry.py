"""Connector registry — resolves a connector implementation by type and mode.

``CONNECTOR_MODE=mock`` returns the mock implementations; ``live`` returns real connectors
(added in Phase 2) behind the identical ports. This is the single seam that makes every
connector replaceable (BRD guardrail / NFR-12).
"""

from __future__ import annotations

from app.connectors.base import Connector
from app.connectors.mock.connectors import (
    MockDocumentConnector,
    MockPipelineConnector,
    MockRepositoryConnector,
    MockTestConnector,
    MockWorkItemConnector,
)
from app.core.config import ConnectorMode, Settings, get_settings
from app.core.errors import ConnectorError
from app.domain.enums import ConnectorType

_MOCK_REGISTRY: dict[ConnectorType, type[Connector]] = {
    ConnectorType.WORK_ITEM: MockWorkItemConnector,
    ConnectorType.REPOSITORY: MockRepositoryConnector,
    ConnectorType.PIPELINE: MockPipelineConnector,
    ConnectorType.TEST: MockTestConnector,
    ConnectorType.DOCUMENT: MockDocumentConnector,
}


class ConnectorRegistry:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def get(self, connector_type: ConnectorType) -> Connector:
        if self._settings.connector_mode == ConnectorMode.MOCK:
            impl = _MOCK_REGISTRY.get(connector_type)
            if impl is None:
                raise ConnectorError(f"No mock connector for type '{connector_type}'.")
            return impl()
        # Live connectors are registered in Phase 2.
        raise ConnectorError(
            f"Live connector for '{connector_type}' is not yet configured (CONNECTOR_MODE=live)."
        )


def get_connector_registry() -> ConnectorRegistry:
    return ConnectorRegistry()
