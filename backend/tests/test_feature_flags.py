"""Unit tests for persistent feature flags and kill switches."""

from __future__ import annotations

import os
from pathlib import Path
from app.core.feature_flags import FeatureFlags


def test_persistent_feature_flags():
    # Force a specific test file path for clean separation
    flags = FeatureFlags()

    # Disable a connector
    flags.disable_connector("AzureDevOps")
    assert not flags.connector_enabled("AzureDevOps")

    # Re-initialize to verify persistence (B9)
    flags_new = FeatureFlags()
    assert not flags_new.connector_enabled("AzureDevOps")

    # Clean up test artifact
    if flags_new._db_path.exists():
        flags_new._db_path.unlink()
