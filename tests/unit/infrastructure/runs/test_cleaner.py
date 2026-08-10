from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from specmetrics.infrastructure.runs.cleaner import (
    RetentionPolicy,
    RunFolder,
    _parse_run_folder,
    clean_runs,
    compute_retention,
    delete_run_folders,
    discover_run_folders,
    dry_run,
)


def _make_run_folder(tmp_path: Path, days_ago: int, suffix: str) -> Path:
    ts = datetime.now(UTC) - timedelta(days=days_ago)
    name = ts.strftime("%Y%m%d-%H%M%S") + f"-{suffix}"
    folder = tmp_path / name
    folder.mkdir(parents=True)
    (folder / "stage.json").write_text("{}")
    return folder


def test_parse_valid_run_folder():
    rf = _parse_run_folder(Path("/runs"), "20260720-131602-14120866")
    assert rf is not None
    assert rf.name == "20260720-131602-14120866"
    assert rf.run_id == "14120866"
    assert rf.timestamp.year == 2026


def test_parse_invalid_name_returns_none():
    assert _parse_run_folder(Path("/runs"), "not-a-run") is None
    assert _parse_run_folder(Path("/runs"), "README.md") is None


def test_parse_bad_date_returns_none():
    assert _parse_run_folder(Path("/runs"), "99999999-999999-xxxx") is None


def test_discover_run_folders_empty_dir(tmp_path):
    runs_dir = tmp_path / ".specmetrics" / "runs"
    runs_dir.mkdir(parents=True)
    assert discover_run_folders(runs_dir) == []


def test_discover_run_folders_skips_non_matching(tmp_path):
    runs_dir = tmp_path / ".specmetrics" / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "not_a_run").mkdir()
    (runs_dir / ".gitkeep").write_text("")
    assert discover_run_folders(runs_dir) == []


def test_discover_run_folders_sorts_descending(tmp_path):
    runs_dir = tmp_path / ".specmetrics" / "runs"
    runs_dir.mkdir(parents=True)
    old = _make_run_folder(runs_dir, days_ago=10, suffix="000001")
    new = _make_run_folder(runs_dir, days_ago=1, suffix="000002")
    folders = discover_run_folders(runs_dir)
    assert len(folders) == 2
    assert folders[0].name == new.name
    assert folders[1].name == old.name


class TestComputeRetention:
    def _make_runs(self, tmp_path, days_list):
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        paths = []
        for i, d in enumerate(days_list):
            p = _make_run_folder(runs_dir, days_ago=d, suffix=f"0000{i:04x}")
            rf = _parse_run_folder(runs_dir, p.name)
            assert rf is not None, f"Failed to parse folder: {p.name}"
            paths.append(rf)
        paths.sort(key=lambda f: f.timestamp, reverse=True)
        return paths

    def test_default_keeps_90_of_100_with_10_old(self, tmp_path):
        now = datetime.now(UTC)
        days = [40] * 10 + [5] * 90
        runs = self._make_runs(tmp_path, days)
        policy = RetentionPolicy(keep_runs=90, keep_days=30)
        to_delete, to_keep = compute_retention(runs, policy, now=now)
        assert len(to_delete) == 10
        assert len(to_keep) == 90

    def test_all_old_keeps_only_90(self, tmp_path):
        now = datetime.now(UTC)
        days = [60] * 200
        runs = self._make_runs(tmp_path, days)
        policy = RetentionPolicy(keep_runs=90, keep_days=30)
        to_delete, to_keep = compute_retention(runs, policy, now=now)
        assert len(to_keep) == 90
        assert len(to_delete) == 110

    def test_all_recent_keeps_all(self, tmp_path):
        now = datetime.now(UTC)
        days = [5] * 5
        runs = self._make_runs(tmp_path, days)
        policy = RetentionPolicy(keep_runs=90, keep_days=30)
        to_delete, to_keep = compute_retention(runs, policy, now=now)
        assert len(to_delete) == 0
        assert len(to_keep) == 5


class TestCleanRuns:
    def test_default_behavior(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        now = datetime.now(UTC)
        for i in range(100):
            days = 40 if i < 10 else 5
            ts = now - timedelta(days=days, hours=i)
            name = ts.strftime("%Y%m%d-%H%M%S") + f"-{i:04x}"
            (runs_dir / name).mkdir()

        policy = RetentionPolicy(keep_runs=90, keep_days=30)
        deleted, failed, _msg = clean_runs(runs_dir, policy, now=now)
        assert deleted == 10
        assert failed == 0
        remaining = list(runs_dir.iterdir())
        assert len(remaining) == 90

    def test_missing_directory(self, tmp_path):
        runs_dir = tmp_path / "nonexistent"
        policy = RetentionPolicy()
        deleted, failed, msg = clean_runs(runs_dir, policy)
        assert deleted == 0
        assert failed == 0
        assert "not found" in msg

    def test_empty_directory(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        policy = RetentionPolicy()
        deleted, failed, msg = clean_runs(runs_dir, policy)
        assert deleted == 0
        assert failed == 0
        assert "not found" in msg


class TestDryRun:
    def test_dry_run_lists_correct_folders(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        now = datetime.now(UTC)
        for i in range(100):
            days = 40 if i < 10 else 5
            ts = now - timedelta(days=days, hours=i)
            name = ts.strftime("%Y%m%d-%H%M%S") + f"-{i:04x}"
            (runs_dir / name).mkdir()

        policy = RetentionPolicy(keep_runs=90, keep_days=30)
        result = dry_run(discover_run_folders(runs_dir), policy, now=now)
        assert result.total_runs == 100
        assert len(result.runs_to_delete) == 10
        assert len(result.runs_to_keep) == 90
        assert "would delete" in result.summary

    def test_dry_run_no_deletion_side_effects(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        now = datetime.now(UTC)
        for i in range(5):
            ts = now - timedelta(days=5)
            name = ts.strftime("%Y%m%d-%H%M%S") + f"-{i:04x}"
            (runs_dir / name).mkdir()

        before = list(runs_dir.iterdir())
        policy = RetentionPolicy(keep_runs=90, keep_days=30)
        clean_runs(runs_dir, policy, dry_run_mode=True, now=now)
        after = list(runs_dir.iterdir())
        assert len(before) == len(after)

    def test_dry_run_nothing_to_clean(self, tmp_path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        runs_dir.mkdir(parents=True)
        now = datetime.now(UTC)
        for i in range(5):
            ts = now - timedelta(days=1)
            name = ts.strftime("%Y%m%d-%H%M%S") + f"-{i:04x}"
            (runs_dir / name).mkdir()

        policy = RetentionPolicy(keep_runs=90, keep_days=30)
        result = dry_run(discover_run_folders(runs_dir), policy, now=now)
        assert result.total_runs == 5
        assert len(result.runs_to_delete) == 0
        assert "Nothing to clean" in result.summary


class TestDeleteRunFolders:
    def test_delete_success(self, tmp_path):
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        folders = []
        for i in range(3):
            p = _make_run_folder(runs_dir, days_ago=i, suffix=f"d00{i:04x}")
            rf = _parse_run_folder(runs_dir, p.name)
            assert rf is not None
            folders.append(rf)

        deleted, failed = delete_run_folders(folders)
        assert deleted == 3
        assert failed == 0
        assert not any((runs_dir / f.name).exists() for f in folders)

    def test_delete_none(self):
        deleted, failed = delete_run_folders([])
        assert deleted == 0
        assert failed == 0


class TestCustomRetention:
    def test_keep_runs_zero_disables_count(self, tmp_path):
        now = datetime.now(UTC)
        days = [40, 30, 20, 10, 5]
        runs = []
        for i, d in enumerate(days):
            ts = now - timedelta(days=d)
            rf = RunFolder(
                name=f"run{i}",
                path=tmp_path / f"run{i}",
                timestamp=ts,
                run_id=f"id{i}",
            )
            runs.append(rf)
        runs.sort(key=lambda f: f.timestamp, reverse=True)
        policy = RetentionPolicy(keep_runs=0, keep_days=30)
        to_delete, to_keep = compute_retention(runs, policy, now=now)
        assert len(to_keep) == 4  # >=30 days ago: days 30, 20, 10, 5
        assert len(to_delete) == 1  # day 40 is older than 30

    def test_keep_days_zero_disables_age(self, tmp_path):
        now = datetime.now(UTC)
        days = [40, 30, 20, 10, 5]
        runs = []
        for i, d in enumerate(days):
            ts = now - timedelta(days=d)
            rf = RunFolder(
                name=f"run{i}",
                path=tmp_path / f"run{i}",
                timestamp=ts,
                run_id=f"id{i}",
            )
            runs.append(rf)
        runs.sort(key=lambda f: f.timestamp, reverse=True)
        policy = RetentionPolicy(keep_runs=3, keep_days=0)
        to_delete, to_keep = compute_retention(runs, policy, now=now)
        assert len(to_keep) == 3
        assert len(to_delete) == 2

    def test_both_zero_deletes_all(self, tmp_path):
        now = datetime.now(UTC)
        days = [10, 5, 2]
        runs = []
        for i, d in enumerate(days):
            ts = now - timedelta(days=d)
            rf = RunFolder(
                name=f"run{i}",
                path=tmp_path / f"run{i}",
                timestamp=ts,
                run_id=f"id{i}",
            )
            runs.append(rf)
        runs.sort(key=lambda f: f.timestamp, reverse=True)
        policy = RetentionPolicy(keep_runs=0, keep_days=0)
        to_delete, to_keep = compute_retention(runs, policy, now=now)
        assert len(to_delete) == 3
        assert len(to_keep) == 0

    def test_custom_retention_7_1(self, tmp_path):
        now = datetime.now(UTC)
        days = [7, 6, 5, 4, 3, 2, 1, 0, 0, 0]  # 10 runs
        runs = []
        for i, d in enumerate(days):
            ts = now - timedelta(days=d, hours=i)
            rf = RunFolder(
                name=f"run{i}",
                path=tmp_path / f"run{i}",
                timestamp=ts,
                run_id=f"id{i}",
            )
            runs.append(rf)
        runs.sort(key=lambda f: f.timestamp, reverse=True)
        policy = RetentionPolicy(keep_runs=7, keep_days=1)
        to_delete, to_keep = compute_retention(runs, policy, now=now)
        assert len(to_keep) == 7
        assert len(to_delete) == 3


class TestKeptHelpers:
    """Kills survivors in ``_runs_kept_by_count``/``_runs_kept_by_age``."""

    def _run(self, tmp_path: Path, name: str, days_ago: int) -> RunFolder:
        now = datetime.now(UTC)
        return RunFolder(
            name=name,
            path=tmp_path / name,
            timestamp=now - timedelta(days=days_ago),
            run_id=name,
        )

    def test_kept_by_count_keep_runs_one(self, tmp_path: Path) -> None:
        from specmetrics.infrastructure.runs.cleaner import _runs_kept_by_count

        runs = [self._run(tmp_path, "r0", 0), self._run(tmp_path, "r1", 1)]
        policy = RetentionPolicy(keep_runs=1, keep_days=0)
        assert _runs_kept_by_count(runs, policy) == {runs[0]}

    def test_kept_by_age_zero_days_excludes_now(self, tmp_path: Path) -> None:
        from specmetrics.infrastructure.runs.cleaner import _runs_kept_by_age

        now = datetime.now(UTC)
        run = RunFolder(
            name="r", path=tmp_path / "r", timestamp=now, run_id="id"
        )
        policy = RetentionPolicy(keep_runs=0, keep_days=0)
        assert _runs_kept_by_age([run], policy, now) == set()

    def test_kept_by_age_keep_days_one_includes_now(self, tmp_path: Path) -> None:
        from specmetrics.infrastructure.runs.cleaner import _runs_kept_by_age

        now = datetime.now(UTC)
        run = RunFolder(
            name="r", path=tmp_path / "r", timestamp=now, run_id="id"
        )
        policy = RetentionPolicy(keep_runs=0, keep_days=1)
        assert _runs_kept_by_age([run], policy, now) == {run}


class TestCombineKeep:
    """Kills survivors in ``_combine_keep`` (mutmut_1..10)."""

    def _run(self, tmp_path: Path, name: str) -> RunFolder:
        return RunFolder(
            name=name,
            path=tmp_path / name,
            timestamp=datetime.now(UTC),
            run_id=name,
        )

    def test_union_only_when_both_positive(self, tmp_path: Path) -> None:
        from specmetrics.infrastructure.runs.cleaner import _combine_keep

        r1 = self._run(tmp_path, "r1")
        r2 = self._run(tmp_path, "r2")
        policy = RetentionPolicy(keep_runs=1, keep_days=30)
        result = _combine_keep(policy, keep_by_count={r1}, keep_by_age={r2})
        assert result == {r1, r2}

    def test_zero_days_returns_count_only(self, tmp_path: Path) -> None:
        from specmetrics.infrastructure.runs.cleaner import _combine_keep

        r1 = self._run(tmp_path, "r1")
        r2 = self._run(tmp_path, "r2")
        policy = RetentionPolicy(keep_runs=30, keep_days=0)
        result = _combine_keep(policy, keep_by_count={r1}, keep_by_age={r2})
        assert result == {r1}

    def test_zero_runs_returns_age_only(self, tmp_path: Path) -> None:
        from specmetrics.infrastructure.runs.cleaner import _combine_keep

        r1 = self._run(tmp_path, "r1")
        r2 = self._run(tmp_path, "r2")
        policy = RetentionPolicy(keep_runs=0, keep_days=30)
        result = _combine_keep(policy, keep_by_count={r1}, keep_by_age={r2})
        assert result == {r2}

    def test_both_zero_returns_empty(self, tmp_path: Path) -> None:
        from specmetrics.infrastructure.runs.cleaner import _combine_keep

        r1 = self._run(tmp_path, "r1")
        policy = RetentionPolicy(keep_runs=0, keep_days=0)
        result = _combine_keep(policy, keep_by_count={r1}, keep_by_age=set())
        assert result == set()
