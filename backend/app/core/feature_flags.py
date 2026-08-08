"""Feature flags & kill switches (BRD §16: kill switch per connector, project, model, agent).

Phase 1 provides a settings-backed default implementation with per-scope overrides held in
Redis/DB later. The interface is intentionally simple and injectable so scopes can be added
without touching call sites.
"""

from __future__ import annotations

from app.core.config import Settings, get_settings


class FeatureFlags:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        # In-memory per-scope kill switches; backed by DB/Redis in later phases.
        self._disabled_connectors: set[str] = set()
        self._disabled_projects: set[str] = set()
        self._disabled_agents: set[str] = set()
        self._disabled_models: set[str] = set()

    # --- global capabilities ---
    @property
    def write_actions_enabled(self) -> bool:
        return self._settings.feature_write_actions_enabled

    @property
    def multi_agent_enabled(self) -> bool:
        return self._settings.feature_multi_agent_enabled

    # --- kill switches ---
    def connector_enabled(self, connector_id: str) -> bool:
        return connector_id not in self._disabled_connectors

    def project_enabled(self, project_id: str) -> bool:
        return project_id not in self._disabled_projects

    def agent_enabled(self, agent: str) -> bool:
        return agent not in self._disabled_agents

    def model_enabled(self, model: str) -> bool:
        return model not in self._disabled_models

    def disable_connector(self, connector_id: str) -> None:
        self._disabled_connectors.add(connector_id)

    def disable_project(self, project_id: str) -> None:
        self._disabled_projects.add(project_id)

    def disable_agent(self, agent: str) -> None:
        self._disabled_agents.add(agent)

    def disable_model(self, model: str) -> None:
        self._disabled_models.add(model)


_flags: FeatureFlags | None = None


def get_feature_flags() -> FeatureFlags:
    global _flags
    if _flags is None:
        _flags = FeatureFlags()
    return _flags
