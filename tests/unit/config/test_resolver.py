from __future__ import annotations

from specmetrics.infrastructure.config.resolver import (
    ConfigCircularRefError,
    Resolver,
    _extract_refs,
)
from specmetrics.infrastructure.config.sources import (
    CliSource,
    EnvironmentSource,
)


class TestExtractRefs:
    def test_no_refs(self):
        assert _extract_refs("simple value") == []

    def test_single_ref(self):
        assert _extract_refs("prefix ${KEY} suffix") == ["KEY"]

    def test_multiple_refs(self):
        refs = _extract_refs("${A} ${B}")
        assert refs == ["A", "B"]


class TestResolver:
    def test_simple_resolution(self):
        resolver = Resolver()
        cli = CliSource({"timeout": 30})
        resolver.add_source(cli, cli.load())
        resolved, provenance, warnings = resolver.resolve()
        assert resolved.get("timeout") == 30
        assert "timeout" in provenance

    def test_higher_precedence_overrides(self):
        resolver = Resolver()
        env = EnvironmentSource()
        cli = CliSource({"timeout": 30})
        resolver.add_source(env, {"timeout": "10"})
        resolver.add_source(cli, {"timeout": 30})
        resolved, _, _ = resolver.resolve()
        assert resolved.get("timeout") == 30  # CLI wins

    def test_circular_ref_detected(self):
        resolver = Resolver()
        import pytest

        resolver.add_source(CliSource({"a": "${b}"}), {"a": "${b}"})
        resolver.add_source(CliSource({"b": "${a}"}), {"b": "${a}"})
        with pytest.raises(ConfigCircularRefError) as exc:
            resolver.resolve()
        assert "a" in str(exc.value)
