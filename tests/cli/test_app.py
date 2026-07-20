from __future__ import annotations

import re

from typer.testing import CliRunner

from specmetrics.cli.app import app

runner = CliRunner()


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class TestCliApp:
    def test_help_succeeds(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "measure" in _strip_ansi(result.output)

    def test_help_shows_metrics_option(self):
        result = runner.invoke(app, ["measure", "--help"])
        assert result.exit_code == 0
        assert "--metrics" in _strip_ansi(result.output)

    def test_version_command(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "SpecMetrics" in _strip_ansi(result.output)

    def test_plugins_list_command(self):
        result = runner.invoke(app, ["plugins", "list"])
        assert result.exit_code == 0

    def test_mcp_help(self):
        result = runner.invoke(app, ["mcp", "--help"])
        assert result.exit_code == 0
        assert "start" in _strip_ansi(result.output)
        assert "stop" in _strip_ansi(result.output)
        assert "status" in _strip_ansi(result.output)
