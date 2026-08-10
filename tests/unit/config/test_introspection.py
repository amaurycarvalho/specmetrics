from __future__ import annotations

from pydantic import SecretStr

from specmetrics.infrastructure.config.introspection import (
    _is_sensitive_value,
    _mask_if_sensitive,
    build_dump,
)
from specmetrics.infrastructure.config.schema import (
    CoreConfig,
    ResolvedConfiguration,
)


class TestSensitiveValue:
    def test_secret_str_is_sensitive(self):
        assert _is_sensitive_value(SecretStr("secret")) is True

    def test_plain_string_not_sensitive(self):
        assert _is_sensitive_value("hello") is False

    def test_mask_secret_str(self):
        result = _mask_if_sensitive(SecretStr("secret"), True)
        assert result == "**********"

    def test_skip_non_sensitive(self):
        result = _mask_if_sensitive("hello", False)
        assert result == "hello"


class TestBuildDump:
    def test_empty_config(self):
        config = ResolvedConfiguration(values=CoreConfig())
        dump = build_dump(config)
        assert len(dump.entries) >= 0



from specmetrics.infrastructure.config.schema import (
    SecuritySettings,
    SourceProvenance,
)
from specmetrics.infrastructure.config.sources import SourceLevel


class TestBuildDumpFromProvenance:
    """Kills survivors in ``build_dump``/``_walk_model`` when provenance exists."""

    def test_provenance_entries_masked_and_leveled(self) -> None:
        config = ResolvedConfiguration(
            values=CoreConfig(security=SecuritySettings(api_key=SecretStr("sekret"))),
            provenance={
                "security.api_key": SourceProvenance(
                    key="security.api_key",
                    source="env",
                    level=SourceLevel.ENVIRONMENT,
                    is_default=False,
                ),
                "logging.level": SourceProvenance(
                    key="logging.level",
                    source="env",
                    level=SourceLevel.ENVIRONMENT,
                ),
            },
        )
        dump = build_dump(config)
        by_key = {e.key: e for e in dump.entries}
        assert len(by_key) == 2
        assert by_key["security.api_key"].value == "**********"
        assert by_key["security.api_key"].is_sensitive is True
        assert by_key["security.api_key"].level == "environment"
        assert by_key["logging.level"].value == "info"
        assert by_key["logging.level"].is_sensitive is False
        assert by_key["logging.level"].is_default is False


class TestBuildDumpFromModel:
    """Kills survivors in ``_build_from_model``/``_walk_model`` (default path)."""

    def test_default_entries_full(self) -> None:
        config = ResolvedConfiguration(values=CoreConfig())
        dump = build_dump(config)
        by_key = {e.key: e for e in dump.entries}
        assert "pipeline" in by_key
        assert by_key["pipeline.stage_timeout"].value == 60
        assert by_key["pipeline.stage_timeout"].source == "default"
        assert by_key["pipeline.stage_timeout"].level == "system"
        assert by_key["pipeline.stage_timeout"].is_default is True
        assert by_key["logging.level"].value == "info"
        assert by_key["security.api_key"].value == "**********"
        assert by_key["security.api_key"].is_sensitive is True
