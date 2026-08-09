"""Feature flags & kill switches (BRD §16: kill switch per connector, project, model, agent).

Persists per-scope kill switches in a JSON file to ensure they survive server restarts (B9).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from app.core.config import Settings, get_settings


class FeatureFlags:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._db_path = Path(__file__).parent.parent.parent.parent / "kill_switches.json"

        # Default in-memory sets
        self._disabled_connectors: set[str] = set()
        self._disabled_projects: set[str] = set()
        self._disabled_agents: set[str] = set()
        self._disabled_models: set[str] = set()

        self._load()

    def _load(self) -> None:
        """Load persistent kill switches from disk."""
        if not self._db_path.exists():
            return
        try:
            with open(self._db_path) as f:
                data = json.load(f)
                self._disabled_connectors = set(data.get("connectors", []))
                self._disabled_projects = set(data.get("projects", []))
                self._disabled_agents = set(data.get("agents", []))
                self._disabled_models = set(data.get("models", []))
        except Exception:
            # Fallback if corrupted or unreadable
            pass

    def _save(self) -> None:
        """Save persistent kill switches to disk."""
        try:
            with open(self._db_path, "w") as f:
                json.dump({
                    "connectors": list(self._disabled_connectors),
                    "projects": list(self._disabled_projects),
                    "agents": list(self._disabled_agents),
                    "models": list(self._disabled_models),
                }, f, indent=2)
        except Exception:
            pass

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
        self._save()

    def disable_project(self, project_id: str) -> None:
        self._disabled_projects.add(project_id)
        self._save()

    def disable_agent(self, agent: str) -> None:
        self._disabled_agents.add(agent)
        self._save()

    def disable_model(self, model: str) -> None:
        self._disabled_models.add(model)
        self._save()

    # Helpers to enable them back if needed
    def enable_connector(self, connector_id: str) -> None:
        self._disabled_connectors.discard(connector_id)
        self._save()

    def enable_project(self, project_id: str) -> None:
        self._disabled_projects.discard(project_id)
        self._save()

    def enable_agent(self, agent: str) -> None:
        self._disabled_agents.discard(agent)
        self._save()

    def enable_model(self, model: str) -> None:
        self._disabled_models.discard(model)
        self._save()


_flags: FeatureFlags | None = None


def get_feature_flags() -> FeatureFlags:
    global _flags
    if _flags is None:
        _flags = FeatureFlags()
    return _flags
