# Implementation Plan: Clean Command for Runs Housekeeping

**Branch**: `033-clean-command` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/033-clean-command/spec.md`

## Summary

Add a `specmetrics clean` CLI command that performs automatic housekeeping of `.specmetrics/runs/` by removing run folders that fall outside configurable retention thresholds: `--keep-runs` (default: 90 most recent runs) and `--keep-days` (default: 30 days). Also supports `--dry-run` for preview. The command follows the same project-path convention as `specmetrics measure`.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Typer (CLI framework), structlog (logging), pathlib (filesystem operations)

**Storage**: Filesystem — `.specmetrics/runs/` with folder names in `YYYYMMDD-HHMMSS-<uuid>` format

**Testing**: pytest with `typer.testing.CliRunner` for CLI invocation tests; temporary directories for filesystem simulation

**Target Platform**: Linux, macOS, Windows (cross-platform via pathlib)

**Project Type**: CLI tool (part of the existing SpecMetrics CLI)

**Performance Goals**: Cleanup of 1000 run folders completes in under 1 second (SC-001)

**Constraints**: Must not modify or corrupt remaining run artifacts; must handle permission errors gracefully without aborting the entire operation; must preserve backward compatibility — existing runs are never modified, only deleted

**Scale/Scope**: Operates on a single local `.specmetrics/runs/` directory; no remote or distributed cleanup

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**:
- **XI (Observability as a Native Capability)**: Lifecycle management of run data prevents unbounded disk consumption, ensuring continuous observability.
- **XIII (Evolution Without Disruption)**: Delete-only operations never modify existing runs. Backward compatibility of persistent data is preserved.

**Compliance Verifications**:
- [x] Specification First: N/A — this is a lifecycle management command, not a measurement feature. It does not consume specifications.
- [x] Evidence First: N/A — cleanup does not involve evidence processing.
- [x] Canonical Representation: N/A — operates on filesystem artifacts, not CFM.
- [x] Plugin-Oriented: N/A — cleanup is a CLI utility command; no plugin extension point is warranted.
- [x] Rule Externalization: N/A — retention policy is set via CLI options, not Rule Packs. This is an operational concern, not a measurement policy.
- [x] Layer Independence: The clean command depends only on the filesystem layer (`.specmetrics/runs/`). It does not import from kernel, application, or plugin layers. Layer independence is fully respected.
- [x] Open by Default: The command is exposed via CLI (already documented) and follows the same interface conventions as other commands.

**GATE Decision**: PASS — all verifications satisfied. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```
specs/033-clean-command/
├── spec.md              # Feature specification
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0 — technology research
├── data-model.md        # Phase 1 — entity definitions
├── contracts/           # Phase 1 — CLI contract (command schema)
├── quickstart.md        # Phase 1 — validation guide
└── tasks.md             # Phase 2 — task breakdown (future)
```

### Source Code (repository root)

```
specmetrics/
├── cli/
│   ├── commands/
│   │   └── clean.py         # New: clean command implementation
│   └── app.py               # Modified: register clean command
└── infrastructure/
    └── runs/
        └── cleaner.py       # New: run folder discovery and deletion logic

tests/
├── cli/
│   └── test_clean.py        # New: CLI integration tests
└── unit/
    └── infrastructure/
        └── runs/
            └── test_cleaner.py  # New: unit tests for cleaner logic
```

**Structure Decision**: Single-project layout following existing patterns. Clean logic is split into two layers:
- `infrastructure/runs/cleaner.py` — core logic (discovery, filtering, deletion) as a pure function/service
- `cli/commands/clean.py` — CLI binding (Typer command wrapping the cleaner)

This follows the existing separation of concerns where `cli/commands/` contain Typer wiring and business logic lives in `kernel/` or `infrastructure/`.

## Complexity Tracking

No constitutional violations to justify.
