# CLI Contract: `specmetrics clean`

## Command Syntax

```
specmetrics clean [OPTIONS]
```

## Arguments

None. The command operates on the `.specmetrics/runs/` directory relative to the project path. The project path defaults to the current working directory (same convention as `specmetrics measure`).

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--keep-runs` | `int` | `90` | Maximum number of most recent runs to retain. `0` disables run-count retention. |
| `--keep-days` | `int` | `30` | Maximum age in days for a run to be retained. `0` disables age-based retention. |
| `--dry-run` | `flag` | `False` | Preview mode — list runs that would be deleted without actually deleting them. |
| `--project-path` | `Path` | `"."` | Path to the SpecMetrics project (same as `measure` command). |
| `--verbose` / `-v` | `flag` | `False` | Detailed progress output. |
| `--quiet` / `-q` | `flag` | `False` | Suppress non-error output. |

## Exit Codes

| Code | Condition |
|------|-----------|
| `0` | Successful cleanup (or nothing to clean, or directory missing/empty) |
| `0` | `--dry-run` completed successfully |
| `1` | One or more run folders failed to delete (permission/lock errors) |

## Output (stdout)

**Normal mode** (`--dry-run` not set):
```
Cleaning .specmetrics/runs/...
Deleted 10 run(s). Kept 90 run(s).
```

**Dry-run mode**:
```
Dry-run: would delete 10 run(s), keeping 90 run(s).
Runs to delete:
  20260720-131602-14120866 (2026-07-20, older than 30 days)
  20260720-131635-484514a6 (2026-07-20, older than 30 days)
  ...
```

**No-op** (nothing to clean):
```
Nothing to clean. 5 run(s) found, all within retention policy.
```

**Missing/empty directory**:
```
.specmetrics/runs/ not found. Nothing to clean.
```

## Error Output (stderr)

Used only for warnings and errors via structlog. Permission errors are logged per-folder:
```
Warning: cannot delete run 20260720-131602-14120866: Permission denied. Skipping.
```

## Behavior Rules

1. Run folders are ordered by folder name descending (newest first) for determining "most recent."
2. A run folder is deleted only if it falls OUTSIDE **both** thresholds (when both are active):
   - Not among the N most recent runs (by folder name timestamp)
   - AND older than D days
3. Non-run files/directories inside `.specmetrics/runs/` are silently skipped.
4. Invalid folder names (not matching `YYYYMMDD-HHMMSS-*`) are silently skipped.
5. Permission errors per folder are caught, logged as warnings, and processing continues.
6. The exit code is non-zero if any deletion fails.
