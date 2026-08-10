"""Configuration helpers for the LLM gateway."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Self

_DEFAULT_RPM_LIMIT = 15
_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BATCH_MAX_CHARS = 100000

_CONFIG_SEARCH_PATHS = [
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "specmetrics",
    Path("/etc/specmetrics"),
]


def load_llm_config_rpm() -> int | None:
    """Read the configured RPM limit from a user or system config file."""
    for base in _CONFIG_SEARCH_PATHS:
        for fname in ("config.yml", "config.yaml", "config.json"):
            path = base / fname
            if path.exists():
                try:
                    import ruamel.yaml

                    yaml = ruamel.yaml.YAML(typ="safe")
                    data = yaml.load(path.read_text(encoding="utf-8"))
                    rpm = (
                        (data or {})
                        .get("plugins", {})
                        .get("extraction_stage", {})
                        .get("llm", {})
                        .get("rpm_limit")
                    )
                    if rpm is not None:
                        return int(rpm)
                except Exception:
                    return None
    return None


class LLMGatewayConfig:
    """Configuration for the LLM gateway."""

    provider: str
    model: str
    api_key: str | None
    api_url: str | None
    rpm_limit: int
    max_tokens: int
    max_retries: int
    batch_max_chars: int

    def __init__(
        self: Self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        api_url: str | None = None,
        rpm_limit: int | None = None,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        batch_max_chars: int = _DEFAULT_BATCH_MAX_CHARS,
    ) -> None:
        """Initialize the gateway configuration with optional overrides."""
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.api_url = api_url
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.batch_max_chars = batch_max_chars

        if rpm_limit is not None:
            self.rpm_limit = rpm_limit
        else:
            env_rpm = os.environ.get("SPECMETRICS_LLM_RPM_LIMIT")
            if env_rpm is not None:
                try:
                    self.rpm_limit = int(env_rpm)
                except (ValueError, TypeError):
                    self.rpm_limit = _DEFAULT_RPM_LIMIT
            else:
                cfg_rpm = load_llm_config_rpm()
                self.rpm_limit = cfg_rpm if cfg_rpm is not None else _DEFAULT_RPM_LIMIT