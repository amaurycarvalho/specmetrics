from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from typer.testing import CliRunner

from specmetrics.cli.app import app

runner = CliRunner()


def _create_run_folder(runs_dir: Path, days_ago: int, suffix: str) -> None:
    ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
    name = ts.strftime("%Y%m%d-%H%M%S") + f"-{suffix}"
    folder = runs_dir / name
    folder.mkdir(parents=True)
    (folder / "stage.json").write_text("{}")


class TestCleanCliDefaults:
    def test_clean_with_defaults_removes_old_runs(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(100):
            days = 40 if i < 10 else 5
            _create_run_folder(runs_dir, days_ago=days, suffix=f"{i:04x}")

        result = runner.invoke(app, ["clean", "--project-path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Cleaned" in result.output
        remaining = list(runs_dir.iterdir())
        assert len(remaining) == 90

    def test_clean_defaults_nothing_to_clean(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(5):
            _create_run_folder(runs_dir, days_ago=1, suffix=f"{i:04x}")

        result = runner.invoke(app, ["clean", "--project-path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Nothing to clean" in result.output
        remaining = list(runs_dir.iterdir())
        assert len(remaining) == 5

    def test_clean_missing_directory(self, tmp_path):
        result = runner.invoke(app, ["clean", "--project-path", str(tmp_path)])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestCleanCliCustom:
    def test_clean_keep_runs_7_keep_days_1(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(10):
            _create_run_folder(runs_dir, days_ago=i, suffix=f"{i:04x}")

        result = runner.invoke(
            app,
            [
                "clean",
                "--project-path",
                str(tmp_path),
                "--keep-runs",
                "7",
                "--keep-days",
                "1",
            ],
        )
        assert result.exit_code == 0
        remaining = list(runs_dir.iterdir())
        assert len(remaining) == 7

    def test_clean_keep_days_zero(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(10):
            _create_run_folder(runs_dir, days_ago=i * 5, suffix=f"{i:04x}")

        result = runner.invoke(
            app,
            [
                "clean",
                "--project-path",
                str(tmp_path),
                "--keep-runs",
                "3",
                "--keep-days",
                "0",
            ],
        )
        assert result.exit_code == 0
        remaining = list(runs_dir.iterdir())
        assert len(remaining) == 3

    def test_clean_both_zero_deletes_all(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(5):
            _create_run_folder(runs_dir, days_ago=i, suffix=f"{i:04x}")

        result = runner.invoke(
            app,
            [
                "clean",
                "--project-path",
                str(tmp_path),
                "--keep-runs",
                "0",
                "--keep-days",
                "0",
            ],
        )
        assert result.exit_code == 0
        remaining = list(runs_dir.iterdir())
        assert len(remaining) == 0


class TestCleanCliDryRun:
    def test_dry_run_lists_deletions(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(100):
            days = 40 if i < 10 else 5
            _create_run_folder(runs_dir, days_ago=days, suffix=f"{i:04x}")

        result = runner.invoke(
            app,
            ["clean", "--project-path", str(tmp_path), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "would delete" in result.output
        remaining = list(runs_dir.iterdir())
        assert len(remaining) == 100

    def test_dry_run_nothing_to_clean(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(5):
            _create_run_folder(runs_dir, days_ago=1, suffix=f"{i:04x}")

        result = runner.invoke(
            app,
            ["clean", "--project-path", str(tmp_path), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "Nothing to clean" in result.output
