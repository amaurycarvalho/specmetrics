from __future__ import annotations

from typer.testing import CliRunner

from specmetrics.cli.app import app

runner = CliRunner()


class TestCliApp:
    def test_help_succeeds(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "measure" in result.output

    def test_version_command(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "SpecMetrics" in result.output

    def test_plugins_list_command(self):
        result = runner.invoke(app, ["plugins", "list"])
        assert result.exit_code == 0

    def test_mcp_help(self):
        result = runner.invoke(app, ["mcp", "--help"])
        assert result.exit_code == 0
        assert "start" in result.output
        assert "stop" in result.output
        assert "status" in result.output
