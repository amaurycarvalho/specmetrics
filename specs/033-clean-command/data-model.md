# Data Model: Clean Command for Runs Housekeeping

## Entities

### RunFolder

Represents a single measurement run directory under `.specmetrics/runs/`.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `name` | `str` | Full folder name (e.g., `20260720-131602-14120866`) | Filesystem listing |
| `path` | `Path` | Absolute path to the run folder | Derived from `runs_dir / name` |
| `timestamp` | `datetime` | Parsed timestamp from folder name prefix (`YYYYMMDD-HHMMSS`) | Parsed from `name[:15]` |
| `run_id` | `str` | UUID portion of folder name (after second `-`) | Parsed from `name[16:]` |
| `is_valid` | `bool` | Whether folder name matches the expected pattern | Regex: `^\d{8}-\d{6}-[a-f0-9-]+$` |

**Validation Rules**:
- Folder name MUST match `^\d{8}-\d{6}-[a-f0-9-]+$` to be considered a valid run folder
- The timestamp portion MUST be parseable as `%Y%m%d-%H%M%S`
- Folders that do not match the pattern are silently skipped (FR-012)

### RetentionPolicy

Defines which run folders are eligible for deletion.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `keep_runs` | `int` | `90` | Maximum number of most recent runs to retain. `0` disables. |
| `keep_days` | `int` | `30` | Maximum age in days for a run to be retained. `0` disables. |

**Deletion Logic**:
```
runs = sorted(runs_by_timestamp, desc)
keep_by_count = runs[:keep_runs] if keep_runs > 0 else []
keep_by_age = [r for r in runs if r.timestamp >= now - timedelta(days=keep_days)] if keep_days > 0 else []

if keep_runs > 0 and keep_days > 0:
    to_keep = set(keep_by_count) | set(keep_by_age)
elif keep_runs > 0:
    to_keep = set(keep_by_count)
elif keep_days > 0:
    to_keep = set(keep_by_age)
else:
    to_keep = set()  # both are 0 → delete everything

to_delete = set(runs) - to_keep
```

### DryRunResult

Result of a `--dry-run` execution.

| Field | Type | Description |
|-------|------|-------------|
| `total_runs` | `int` | Total valid run folders found |
| `runs_to_delete` | `list[RunFolder]` | Run folders that would be deleted |
| `runs_to_keep` | `list[RunFolder]` | Run folders that would be kept |
| `summary` | `str` | Human-readable summary |

## State Transitions

No state transitions — the clean command is a stateless operation:
1. List → Filter → Delete (or preview)
2. Each invocation is independent
3. No state is persisted between invocations
