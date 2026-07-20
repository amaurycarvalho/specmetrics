from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

RUN_FOLDER_PATTERN = re.compile(r"^\d{8}-\d{6}-[a-f0-9-]+$")
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


@dataclass(frozen=True)
class RunFolder:
    name: str
    path: Path
    timestamp: datetime
    run_id: str
    is_valid: bool = True


@dataclass
class RetentionPolicy:
    keep_runs: int = 90
    keep_days: int = 30


@dataclass
class DryRunResult:
    total_runs: int
    runs_to_delete: list[RunFolder]
    runs_to_keep: list[RunFolder]
    summary: str


def _parse_run_folder(runs_dir: Path, name: str) -> RunFolder | None:
    if not RUN_FOLDER_PATTERN.match(name):
        return None
    try:
        ts = datetime.strptime(name[:15], TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    run_id = name[16:]
    return RunFolder(
        name=name,
        path=runs_dir / name,
        timestamp=ts,
        run_id=run_id,
    )


def discover_run_folders(runs_dir: Path) -> list[RunFolder]:
    if not runs_dir.is_dir():
        return []
    folders: list[RunFolder] = []
    for entry in runs_dir.iterdir():
        if not entry.is_dir():
            continue
        rf = _parse_run_folder(runs_dir, entry.name)
        if rf is not None:
            folders.append(rf)
    folders.sort(key=lambda f: f.timestamp, reverse=True)
    return folders


def compute_retention(
    runs: list[RunFolder],
    policy: RetentionPolicy,
    now: datetime | None = None,
) -> tuple[list[RunFolder], list[RunFolder]]:
    if now is None:
        now = datetime.now(timezone.utc)

    keep_by_count: set[RunFolder] = set()
    keep_by_age: set[RunFolder] = set()

    if policy.keep_runs > 0:
        keep_by_count = set(runs[: policy.keep_runs])
    if policy.keep_days > 0:
        cutoff = now - timedelta(days=policy.keep_days)
        keep_by_age = {r for r in runs if r.timestamp >= cutoff}

    if policy.keep_runs > 0 and policy.keep_days > 0:
        to_keep = keep_by_count | keep_by_age
    elif policy.keep_runs > 0:
        to_keep = keep_by_count
    elif policy.keep_days > 0:
        to_keep = keep_by_age
    else:
        to_keep = set()

    to_delete = [r for r in runs if r not in to_keep]
    to_keep_list = [r for r in runs if r in to_keep]
    return to_delete, to_keep_list


def delete_run_folders(folders: list[RunFolder]) -> tuple[int, int]:
    deleted = 0
    failed = 0
    for rf in folders:
        try:
            shutil.rmtree(rf.path)
            deleted += 1
        except (OSError, PermissionError) as exc:
            logger.warning(
                "cannot_delete_run_folder",
                run_folder=rf.name,
                error=str(exc),
            )
            failed += 1
    return deleted, failed


def dry_run(
    runs: list[RunFolder],
    policy: RetentionPolicy,
    now: datetime | None = None,
) -> DryRunResult:
    to_delete, to_keep = compute_retention(runs, policy, now=now)
    total = len(runs)
    lines: list[str] = []
    if to_delete:
        lines.append(
            f"Dry-run: would delete {len(to_delete)} run(s), keeping {len(to_keep)} run(s)."
        )
        lines.append("Runs to delete:")
        for rf in to_delete:
            age_hint = ""
            if policy.keep_days > 0:
                age_hint = f" (older than {policy.keep_days} days)"
            lines.append(f"  {rf.name} ({rf.timestamp.date()}){age_hint}")
    else:
        lines.append(
            f"Nothing to clean. {total} run(s) found, all within retention policy."
        )
    return DryRunResult(
        total_runs=total,
        runs_to_delete=to_delete,
        runs_to_keep=to_keep,
        summary="\n".join(lines),
    )


def clean_runs(
    runs_dir: Path,
    policy: RetentionPolicy,
    dry_run_mode: bool = False,
    now: datetime | None = None,
) -> tuple[int, int, str]:
    runs = discover_run_folders(runs_dir)
    if not runs:
        msg = f"{runs_dir}/ not found. Nothing to clean."
        return 0, 0, msg

    if dry_run_mode:
        result = dry_run(runs, policy, now=now)
        return 0, 0, result.summary

    to_delete, to_keep = compute_retention(runs, policy, now=now)
    if not to_delete:
        msg = (
            f"Nothing to clean. {len(runs)} run(s) found, all within retention policy."
        )
        return 0, 0, msg

    deleted, failed = delete_run_folders(to_delete)
    msg = f"Cleaned {deleted} run(s). Kept {len(to_keep)} run(s)."
    return deleted, failed, msg
