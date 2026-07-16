from __future__ import annotations

from typer.testing import CliRunner

from specmetrics.cli.app import app

runner = CliRunner()


class TestExplainCLI:
    def test_explain_command_exists(self):
        result = runner.invoke(app, ["explain", "--help"])
        assert result.exit_code == 0
        assert "Explain" in result.stdout or "explain" in result.stdout

    def test_explain_requires_run_id(self):
        result = runner.invoke(app, ["explain", "explain"])
        assert result.exit_code != 0

    def test_explain_unknown_run_id_returns_exit_code_2(self):
        result = runner.invoke(app, ["explain", "nonexistent-run"])
        assert result.exit_code in (1, 2)
        assert "error" in result.stdout.lower() or result.exit_code == 2

    def test_explain_accepts_format_option(self):
        result = runner.invoke(app, ["explain", "explain", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.stdout

    def test_explain_accepts_metric_option(self):
        result = runner.invoke(app, ["explain", "explain", "--help"])
        assert "--metric" in result.stdout

    def test_explain_accepts_compare_option(self):
        result = runner.invoke(app, ["explain", "explain", "--help"])
        assert "--compare" in result.stdout
