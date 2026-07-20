# Feature Specification: Clean Command for Runs Housekeeping

**Feature Branch**: `033-clean-command`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Crie o comando `clean` para fazer housekeeping automático da pasta .specmetrics/runs/ com as opções `--keep_runs` (default=90) e `--keep_days` (default=30)"

## User Scenarios & Testing

### User Story 1 - Developer cleans old runs manually with defaults (Priority: P1)

A developer has been running `specmetrics measure` regularly over several months, accumulating hundreds of run folders in `.specmetrics/runs/`. They run `specmetrics clean` to remove old runs, expecting that only the last 90 runs and runs older than 30 days are removed, keeping the most recent 90 runs intact regardless of age.

**Why this priority**: This is the primary use case — a simple, safe default that prevents disk bloat without requiring the user to understand the retention policy details.

**Independent Test**: Can be fully tested by creating 100+ run folders with varying timestamps (some within 30 days, some older than 30 days, some older but among the most recent 90), running `specmetrics clean` with defaults, and verifying that only runs outside both thresholds are deleted.

**Acceptance Scenarios**:

1. **Given** 100 run folders exist where 10 are older than 30 days and the remaining 90 are within 30 days, **When** `specmetrics clean` is executed with defaults, **Then** the 10 runs older than 30 days are deleted and the 90 recent runs are kept.
2. **Given** 200 run folders exist where all are older than 30 days, **When** `specmetrics clean` is executed with defaults, **Then** only the most recent 90 runs are kept and the remaining 110 are deleted.
3. **Given** only 5 run folders exist, all within 30 days, **When** `specmetrics clean` is executed with defaults, **Then** no run folders are deleted.

---

### User Story 2 - Developer customizes retention policy (Priority: P1)

An operator in a CI/CD environment produces hundreds of runs daily. They run `specmetrics clean --keep_runs 7 --keep_days 1` to keep only the last 7 runs and delete anything older than 1 day, aggressively freeing disk space.

**Why this priority**: Customizable retention is essential for different usage patterns — local development requires loose retention, while CI/CD needs strict limits.

**Independent Test**: Can be tested by creating 20 run folders with timestamps spanning 7 days, then running with `--keep_runs 7 --keep_days 1` and verifying only the intersection of the 7 most recent runs and runs from the last day remain.

**Acceptance Scenarios**:

1. **Given** 20 run folders spanning 7 days, **When** `specmetrics clean --keep_runs 7 --keep_days 1` is executed, **Then** only runs within the last day AND among the last 7 are kept.
2. **Given** run folders exist, **When** `specmetrics clean --keep_runs 0` is executed, **Then** only the time-based retention (`--keep_days`) is applied (no run-count limit).
3. **Given** run folders exist, **When** `specmetrics clean --keep_days 0` is executed, **Then** only the run-count retention (`--keep_runs`) is applied (no age limit).

---

### User Story 3 - Developer previews what would be deleted (Priority: P2)

Before running destructive cleanup, a developer runs `specmetrics clean --dry-run` to see which runs would be deleted without actually removing them. The output lists each run folder that would be deleted and a summary of total runs to be removed.

**Why this priority**: Safety-first — users need confidence before destructive operations. Lower priority because the defaults are designed to be safe (keeping recent runs).

**Independent Test**: Can be tested by creating runs and running `specmetrics clean --dry-run`, verifying the command lists the same runs that a real `specmetrics clean` would delete, without actually deleting any files.

**Acceptance Scenarios**:

1. **Given** 100 runs exist with 10 older than 30 days, **When** `specmetrics clean --dry-run` is executed, **Then** the command outputs the 10 run IDs that would be deleted and a summary count, without deleting any files.
2. **Given** the same state, **When** `specmetrics clean --dry-run` is followed by `specmetrics clean`, **Then** the same 10 runs are deleted in the second command.

---

### Edge Cases

- What happens when `.specmetrics/runs/` does not exist?
- What happens when `.specmetrics/runs/` is empty?
- What happens when `--keep_runs 0` and `--keep_days 0` are both provided — is everything deleted?
- How does the system handle run folders with invalid/missing timestamps in their folder names?
- What happens when a run folder cannot be deleted (permission error, locked file)?
- How does the system handle non-run directories or files inside `.specmetrics/runs/` (e.g., a `.gitkeep` or stray file)?

## Constitution Check

**Engaged Principles**:
- **Principle XI (Observability as a Native Capability)**: The clean command manages the lifecycle of measurement run data, preventing unbounded disk usage that would impair continuous observability.
- **Principle XIII (Evolution Without Disruption)**: Clean only removes old runs — it never modifies, corrupts, or invalidates remaining runs. Backward compatibility of persistent data is preserved.

**Compliance Notes**:
- The clean command operates exclusively on `.specmetrics/runs/` artifacts and never touches specification source files, configuration, or plugin data — respecting layer independence (XIV).
- Deletion is performed based on stable run metadata (folder timestamp/name) without depending on internal pipeline state — preserving the immutable pipeline invariant.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST provide a `clean` CLI command under `specmetrics clean`.
- **FR-002**: The `clean` command MUST accept an optional `--keep-runs` option (default: 90) specifying the maximum number of most recent run folders to retain.
- **FR-003**: The `clean` command MUST accept an optional `--keep-days` option (default: 30) specifying the maximum age in days of run folders to retain.
- **FR-004**: When both `--keep-runs` and `--keep-days` are specified (or defaults are used), a run folder MUST only be deleted if it falls outside BOTH thresholds — i.e., it is NOT among the N most recent runs AND is older than D days.
- **FR-005**: When `--keep-runs` is set to 0, run-count-based retention MUST be disabled and ONLY the `--keep-days` threshold applies.
- **FR-006**: When `--keep-days` is set to 0, age-based retention MUST be disabled and ONLY the `--keep-runs` threshold applies.
- **FR-007**: The command MUST accept a `--dry-run` flag that lists the runs that would be deleted without actually deleting them, along with a summary of total runs to remove and total runs to keep.
- **FR-008**: The command MUST handle the case where `.specmetrics/runs/` does not exist by printing a message and exiting successfully (exit code 0).
- **FR-009**: The command MUST handle the case where `.specmetrics/runs/` is empty by printing a message and exiting successfully (exit code 0).
- **FR-010**: Run folders MUST be ordered by their timestamp for determining "most recent" — the folder name format `YYYYMMDD-HHMMSS-*` is the authoritative ordering key.
- **FR-011**: If a run folder cannot be deleted due to permission errors or locked files, the command MUST log a warning with the folder path and continue processing remaining folders. The exit code MUST be non-zero if any deletion fails.
- **FR-012**: The command MUST skip non-run files and directories that do not match the run folder naming convention without raising errors.

### Key Entities

- **Run Folder**: A timestamped directory under `.specmetrics/runs/` named in `YYYYMMDD-HHMMSS-<uuid>` format, containing stage artifacts from a pipeline execution. Key attributes: creation timestamp (from folder name), run ID (from folder name), path on disk.
- **Retention Policy**: A combination of `keep_runs` (run count limit) and `keep_days` (age limit) that determines which run folders are eligible for deletion. Configurable via CLI options.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A user can invoke `specmetrics clean` with default options and have run folders outside both retention thresholds removed in under 1 second for up to 1000 run folders.
- **SC-002**: The `--dry-run` flag accurately predicts deletion without side effects — verified by comparing `--dry-run` output against actual deletion in identical state.
- **SC-003**: A user can customize retention via `--keep-runs` and `--keep-days` and observe the specified retention behavior immediately on the next invocation.
- **SC-004**: The command exits with code 0 for successful cleanup, non-zero when any deletion fails, and 0 when there is nothing to clean — consistently and predictably.

## Assumptions

- Run folder names follow the `YYYYMMDD-HHMMSS-<uuid>` convention established by the existing `measure` command.
- The `.specmetrics/runs/` directory is managed exclusively by specmetrics — external files placed there are at the user's own risk and are skipped.
- Disk space recovery is the primary motivation — no journaling or undo capability is required for deleted runs (the `--dry-run` feature provides preview safety).
- Deletion means permanent removal (no trash/recycle bin). Users who need recovery should back up `.specmetrics/runs/` independently.
- The command operates on the project path where `.specmetrics/` resides (same as `measure`), defaulting to the current working directory.
