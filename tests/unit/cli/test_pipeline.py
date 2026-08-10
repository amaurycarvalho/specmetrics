from __future__ import annotations

import logging
from pathlib import Path

from specmetrics.application.enums import OutputFormat, StageName
from specmetrics.cli import _pipeline


class TestSetupLogFile:
    def test_creates_log_file(self, tmp_path):
        root = logging.getLogger()
        original_handlers = list(root.handlers)
        try:
            path = _pipeline._setup_log_file(tmp_path, "run.log")
            assert Path(path) == tmp_path / ".specmetrics" / "logs" / "run.log"
            assert Path(path).exists()
        finally:
            for h in root.handlers[:]:
                if h not in original_handlers:
                    root.removeHandler(h)
                    h.close()


class TestGetConfigSystem:
    def test_returns_same_instance(self):
        sys1 = _pipeline.get_config_system()
        sys2 = _pipeline.get_config_system()
        assert sys1 is sys2


class TestResolveOutput:
    def test_none(self):
        fmt, path = _pipeline.resolve_output(None)
        assert fmt == OutputFormat.TEXT
        assert path is None

    def test_no_colon(self):
        fmt, path = _pipeline.resolve_output("json")
        assert fmt == OutputFormat.JSON
        assert path is None

    def test_with_path(self):
        fmt, path = _pipeline.resolve_output("json:/tmp/out.json")
        assert fmt == OutputFormat.JSON
        assert path == Path("/tmp/out.json")


class TestResolveConfigSystem:
    def test_no_config_path_uses_singleton(self, monkeypatch):
        fake = object()
        monkeypatch.setattr(_pipeline, "get_config_system", lambda: fake)
        result = _pipeline.resolve_config_system(Path("/x"), None)
        assert result is fake

    def test_explicit_config_path_loads(self, tmp_path):
        cfg_file = tmp_path / "specmetrics.yml"
        cfg_file.write_text("output:\n  format: text\n")
        cfg = _pipeline.resolve_config_system(tmp_path, cfg_file)
        assert cfg is not None
        provider = cfg.load()
        assert provider is not None


class TestConfigureLogging:
    def test_quiet_sets_error(self):
        root = logging.getLogger()
        before = root.level
        try:
            _pipeline.configure_logging(None, Path("."), False, True)
            assert root.level == logging.ERROR
        finally:
            root.setLevel(before)

    def test_verbose_sets_info(self):
        root = logging.getLogger()
        before = root.level
        try:
            _pipeline.configure_logging(None, Path("."), True, False)
            assert root.level == logging.INFO
        finally:
            root.setLevel(before)

    def test_log_file_sets_debug(self, tmp_path):
        root = logging.getLogger()
        before = root.level
        original_handlers = list(root.handlers)
        try:
            _pipeline.configure_logging("run.log", tmp_path, False, False)
            assert root.level == logging.DEBUG
            assert (tmp_path / ".specmetrics" / "logs" / "run.log").exists()
        finally:
            root.setLevel(before)
            for h in list(root.handlers):
                if h not in original_handlers:
                    root.removeHandler(h)
                    h.close()

    def test_default_no_change(self):
        root = logging.getLogger()
        before = root.level
        try:
            _pipeline.configure_logging(None, Path("."), False, False)
            assert root.level == before
        finally:
            root.setLevel(before)


class TestResolveStages:
    def test_stage_only(self):
        stages, from_stage = _pipeline.resolve_stages("discover", None)
        assert stages == [StageName.DISCOVER]
        assert from_stage is None

    def test_from_stage_only(self):
        stages, from_stage = _pipeline.resolve_stages(None, "cfm")
        assert stages is None
        assert from_stage == StageName.CFM

    def test_both_none(self):
        stages, from_stage = _pipeline.resolve_stages(None, None)
        assert stages is None
        assert from_stage is None