from __future__ import annotations

from pathlib import Path

from specmetrics.infrastructure.config.sources import (
    CliSource,
    EnvironmentSource,
    FileSource,
    SourceLevel,
    _flatten_dict,
)


class TestSourceLevel:
    def test_precedence_order(self):
        assert SourceLevel.SYSTEM < SourceLevel.USER
        assert SourceLevel.USER < SourceLevel.PROJECT
        assert SourceLevel.PROJECT < SourceLevel.ENVIRONMENT
        assert SourceLevel.ENVIRONMENT < SourceLevel.CLI


class TestFileSource:
    def test_nonexistent_file_returns_empty(self):
        source = FileSource(Path("/nonexistent/config.yml"), SourceLevel.PROJECT)
        assert source.load() == {}

    def test_name_includes_level(self):
        source = FileSource(Path("/tmp/test.yml"), SourceLevel.PROJECT)
        assert "project" in source.name


class TestEnvironmentSource:
    def test_empty_prefix_finds_nothing(self, monkeypatch):
        monkeypatch.setenv("SPECMETRICS_TEST_VAR", "value")
        source = EnvironmentSource(prefix="OTHER_")
        data = source.load()
        assert "test.var" not in data

    def test_finds_matching_vars(self, monkeypatch):
        monkeypatch.setenv("SPECMETRICS_LOGGING_LEVEL", "debug")
        source = EnvironmentSource()
        data = source.load()
        assert data.get("logging.level") == "debug"


class TestCliSource:
    def test_empty_args(self):
        source = CliSource({})
        assert source.load() == {}

    def test_nested_args(self):
        source = CliSource({"pipeline": {"timeout": 30}})
        data = source.load()
        assert data.get("pipeline.timeout") == 30


class TestFlattenDict:
    def test_flat_dict(self):
        assert _flatten_dict({"a": 1, "b": 2}, "") == {"a": 1, "b": 2}

    def test_nested_dict(self):
        assert _flatten_dict({"a": {"b": 1, "c": 2}}, "") == {"a.b": 1, "a.c": 2}

    def test_prefix(self):
        assert _flatten_dict({"x": 1}, "root") == {"root.x": 1}
