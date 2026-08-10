from __future__ import annotations

import logging
from pathlib import Path

from specmetrics.application.enums import OutputFormat
from specmetrics.cli import _pipeline


class TestSetupLogFile:
    def test_creates_nested_logs_directory(self, tmp_path: Path, monkeypatch):
        """Kills _setup_log_file__mutmut_9/11/13 (mkdir parents/exist_ok mutations)."""
        _pipeline._setup_log_file(tmp_path, "measure.log")
        assert (tmp_path / ".specmetrics" / "logs" / "measure.log").exists()

    def test_strips_ansi_escape_sequences(self, tmp_path: Path, monkeypatch):
        """Kills _setup_log_file__mutmut_36/37 (addFilter mutations) and 19."""
        _pipeline._setup_log_file(tmp_path, "measure.log")
        logger = logging.getLogger(f"test_ansi_{tmp_path.name}")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.FileHandler(tmp_path / ".specmetrics" / "logs" / "measure.log", encoding="utf-8"))
        logger.handlers[-1].setFormatter(logging.Formatter("%(message)s"))
        logger.handlers[-1].addFilter(lambda rec: setattr(rec, "msg", ""))
        # The filter chain installed by _setup_log_file already ran; just log raw.
        logging.getLogger().info("\x1b[31mcolored message\x1b[0m")
        content = (tmp_path / ".specmetrics" / "logs" / "measure.log").read_text()
        assert "\x1b[" not in content
        assert "colored message" in content

    def test_message_only_format_no_level_prefix(self, tmp_path: Path, monkeypatch):
        """Targets _setup_log_file__mutmut_31/32/35 (Formatter/setFormatter -> None)."""
        _pipeline._setup_log_file(tmp_path, "measure.log")
        logging.getLogger().info("plain message body")
        content = (tmp_path / ".specmetrics" / "logs" / "measure.log").read_text()
        assert "plain message body" in content
        assert "INFO" not in content


class TestGetConfigSystem:
    def test_returns_same_shared_instance(self, monkeypatch):
        """Kills get_config_system__mutmut_2 (cache assigned None)."""
        monkeypatch.setattr(_pipeline, "_config_system", None)
        first = _pipeline.get_config_system()
        second = _pipeline.get_config_system()
        assert first is second

    def test_returns_configuration_system_instance(self, monkeypatch):
        """Targets get_config_system__mutmut_2 return type."""
        monkeypatch.setattr(_pipeline, "_config_system", None)
        from specmetrics.infrastructure.config.loader import ConfigurationSystem

        assert isinstance(_pipeline.get_config_system(), ConfigurationSystem)


class TestResolveOutput:
    def test_none_returns_text_format(self):
        """Targets resolve_output__mutmut_8/9/11 default for empty output."""
        fmt, path = _pipeline.resolve_output(None)
        assert fmt == OutputFormat.TEXT
        assert path is None

    def test_format_only_no_path(self):
        """Targets resolve_output__mutmut_8/9/11 format-only branch."""
        fmt, path = _pipeline.resolve_output("json")
        assert fmt == OutputFormat.JSON
        assert path is None

    def test_format_path_with_single_colon(self):
        """Targets resolve_output__mutmut_8/11 single-colon split."""
        fmt, path = _pipeline.resolve_output("json:/tmp/out.json")
        assert fmt == OutputFormat.JSON
        assert path == Path("/tmp/out.json")

    def test_path_containing_colon_keeps_full_path(self):
        """Kills resolve_output__mutmut_9 (split -> rsplit)."""
        fmt, path = _pipeline.resolve_output("json:dir:sub/out.json")
        assert fmt == OutputFormat.JSON
        assert path == Path("dir:sub/out.json")

    def test_format_path_with_many_colons_uses_first_split(self):
        """Kills resolve_output__mutmut_8/11 (maxsplit removed / changed to 2)."""
        fmt, path = _pipeline.resolve_output("json:a:b")
        assert fmt == OutputFormat.JSON
        assert path == Path("a:b")


class TestResolveConfigSystem:
    def test_none_config_path_returns_shared_system(self, monkeypatch):
        """Targets resolve_config_system__mutmut_3/4/5/6 config_path=None branch."""
        fake = object()
        monkeypatch.setattr(_pipeline, "get_config_system", lambda: fake)
        assert _pipeline.resolve_config_system(Path("."), None) is fake

    def test_config_path_builds_system_with_project_and_path(self, monkeypatch):
        """Kills resolve_config_system__mutmut_3/4/5/6 (kwargs -> None/removed)."""
        calls: list[dict] = []

        class FakeConfigSystem:
            def __init__(self, **kwargs):
                calls.append(kwargs)

            def load(self):
                return None

        monkeypatch.setattr(_pipeline, "ConfigurationSystem", FakeConfigSystem)
        project = Path("/proj")
        cfg_path = Path("/proj/specmetrics.yml")
        result = _pipeline.resolve_config_system(project, cfg_path)
        assert result is not None
        assert calls == [{"project_root": project, "config_path": cfg_path}]
