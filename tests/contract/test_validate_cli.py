from __future__ import annotations

from typer.testing import CliRunner

from specmetrics.cli.app import app

runner = CliRunner()


class TestValidateCli:
    def test_validate_help(self):
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0

    def test_validate_nonexistent_file(self, tmp_path):
        result = runner.invoke(app, ["validate", str(tmp_path / "nonexistent.md")])
        assert result.exit_code != 0
