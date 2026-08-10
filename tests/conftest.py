from __future__ import annotations

import pytest
import structlog

# Snapshot the pristine structlog configuration before any test module imports
# code that reconfigures structlog globally (e.g. ``specmetrics.mcp.server`` and
# ``specmetrics.cli.app`` call ``structlog.configure`` at import time). Some of
# those reconfigurations install a filtering wrapper that drops debug/warning
# events, which breaks later tests relying on ``structlog.testing.capture_logs``.
_PRISTINE_STRUCTLOG_CONFIG = structlog.get_config()


@pytest.fixture(autouse=True)
def _isolate_structlog_config() -> None:
    """Restore the pristine global structlog configuration after each test."""
    yield
    structlog.reset_defaults()
    structlog.configure(**_PRISTINE_STRUCTLOG_CONFIG)
