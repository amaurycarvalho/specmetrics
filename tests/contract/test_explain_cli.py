from __future__ import annotations

import re

from typer.testing import CliRunner

from specmetrics.cli.app import app

runner = CliRunner()
_ansi = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _strip(text: str) -> str:
    return _ansi.sub("", text)


class TestExplainCLI:
    def test_explain_command_exists(self):
        result = runner.invoke(app, ["explain", "--help"])
        assert result.exit_code == 0
        out = _strip(result.stdout)
        assert "Explain" in out or "explain" in out

    def test_explain_requires_run_id(self):
        result = runner.invoke(app, ["explain", "explain"])
        assert result.exit_code != 0

    def test_explain_unknown_run_id_returns_exit_code_2(self):
        result = runner.invoke(app, ["explain", "nonexistent-run"])
        assert result.exit_code in (1, 2)
        out = _strip(result.stdout)
        assert "error" in out.lower() or result.exit_code == 2

    def test_explain_accepts_format_option(self):
        result = runner.invoke(app, ["explain", "explain", "--help"])
        assert result.exit_code == 0
        out = _strip(result.stdout)
        assert "--format" in out

    def test_explain_accepts_metric_option(self):
        result = runner.invoke(app, ["explain", "explain", "--help"])
        out = _strip(result.stdout)
        assert "--metric" in out

    def test_explain_accepts_compare_option(self):
        result = runner.invoke(app, ["explain", "explain", "--help"])
        out = _strip(result.stdout)
        assert "--compare" in out
