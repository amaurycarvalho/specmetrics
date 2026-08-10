from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from typer.testing import CliRunner

from specmetrics.cli.app import app

runner = CliRunner()


def _create_run_folder(runs_dir: Path, days_ago: int, suffix: str) -> None:
    ts = datetime.now(UTC) - timedelta(days=days_ago)
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


def _create_run_folder_at(runs_dir: Path, ts, suffix: str) -> None:
    name = ts.strftime("%Y%m%d-%H%M%S") + f"-{suffix}"
    folder = runs_dir / name
    folder.mkdir(parents=True)
    (folder / "stage.json").write_text("{}")


class TestCleanCliMutationKillers:
    def test_clean_default_project_path_is_dot(self, tmp_path, monkeypatch):
        """Kills clean_command__mutmut_1 (project_path default '.' -> 'XX.XX')."""
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(90):
            _create_run_folder(runs_dir, days_ago=1, suffix=f"{i:04x}")
        for i in range(5):
            _create_run_folder(runs_dir, days_ago=40, suffix=f"{90 + i:04x}")

        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["clean"])
        assert result.exit_code == 0
        assert "Cleaned" in result.output
        assert len(list(runs_dir.iterdir())) == 90

    def test_default_keep_runs_is_90(self, tmp_path):
        """Kills clean_command__mutmut_2 (keep_runs default 90 -> 91)."""
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(90):
            _create_run_folder(runs_dir, days_ago=1, suffix=f"{i:04x}")
        _create_run_folder(runs_dir, days_ago=40, suffix="0090")

        result = runner.invoke(app, ["clean", "--project-path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Cleaned" in result.output
        assert len(list(runs_dir.iterdir())) == 90

    def test_default_keep_days_is_30(self, tmp_path):
        """Kills clean_command__mutmut_3 (keep_days default 30 -> 31)."""
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(90):
            _create_run_folder(runs_dir, days_ago=1, suffix=f"{i:04x}")
        for i in range(5):
            ts = datetime.now(UTC) - timedelta(days=30, hours=6)
            _create_run_folder_at(runs_dir, ts, f"a{i:04x}")

        result = runner.invoke(app, ["clean", "--project-path", str(tmp_path)])
        assert result.exit_code == 0
        assert len(list(runs_dir.iterdir())) == 90

    def test_default_dry_run_is_false(self, tmp_path):
        """Kills clean_command__mutmut_4/5/6 (dry_run default False -> True)."""
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(90):
            _create_run_folder(runs_dir, days_ago=1, suffix=f"{i:04x}")
        for i in range(5):
            _create_run_folder(runs_dir, days_ago=40, suffix=f"{90 + i:04x}")

        result = runner.invoke(app, ["clean", "--project-path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Cleaned" in result.output
        assert len(list(runs_dir.iterdir())) == 90

    def test_missing_directory_exits_zero(self, tmp_path):
        """Kills clean_command__mutmut_25/44 (Exit code 0 -> None)."""
        result = runner.invoke(app, ["clean", "--project-path", str(tmp_path)])
        assert result.exit_code == 0
        assert "not found" in result.output

    def test_clean_uses_current_time_for_retention(self, tmp_path):
        """Targets clean_command__mutmut_19/31/35 (now passed to clean_runs)."""
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        for i in range(90):
            _create_run_folder(runs_dir, days_ago=1, suffix=f"{i:04x}")
        for i in range(5):
            _create_run_folder(runs_dir, days_ago=40, suffix=f"{90 + i:04x}")

        result = runner.invoke(app, ["clean", "--project-path", str(tmp_path)])
        assert result.exit_code == 0
        assert len(list(runs_dir.iterdir())) == 90


class TestCleanCliFailure:
    def test_failed_deletions_exit_code_one(self, tmp_path, monkeypatch):
        """Kills clean_command__mutmut_39/41/42/43 (failed>0 exit gate + code)."""
        import specmetrics.cli.commands.clean as clean_mod

        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        _create_run_folder(runs_dir, days_ago=40, suffix="0000")

        monkeypatch.setattr(clean_mod, "clean_runs", lambda **kwargs: (0, 1, "Failed to clean 1 run(s)."))
        result = runner.invoke(app, ["clean", "--project-path", str(tmp_path)])
        assert result.exit_code == 1
        assert "Failed to clean 1 run(s)." in result.output

    def test_failed_deletions_ignored_in_dry_run(self, tmp_path, monkeypatch):
        """Kills clean_command__mutmut_39 (dry_run gate)."""
        import specmetrics.cli.commands.clean as clean_mod

        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        _create_run_folder(runs_dir, days_ago=40, suffix="0000")

        monkeypatch.setattr(clean_mod, "clean_runs", lambda **kwargs: (0, 1, "Dry-run preview"))
        result = runner.invoke(
            app, ["clean", "--project-path", str(tmp_path), "--dry-run"]
        )
        assert result.exit_code == 0
