# Implementation Plan: Measure ID & Export Commands

**Branch**: `031-measure-id-export` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/031-measure-id-export/spec.md`

## Summary

Add measure-run tracking to the `specmetrics measure` command (generate unique ID, persist per-stage JSON to `.specmetrics/runs/<id>/`, emit `measure.id` and `measure.id_path` in `specmetrics-output.json`), create `export list` (list available run IDs), and refactor `export run` to read from persisted runs (with fallback to direct pipeline execution). CSV/XML export uses tabular normalization per stage.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Typer (CLI), Pydantic v2 (models), structlog (logging)

**Storage**: Filesystem — `.specmetrics/runs/<measure-id>/` for per-stage JSON files; `exports/` for export output

**Testing**: pytest (unit + integration + contract tests)

**Target Platform**: Linux server / developer workstation (CLI tool)

**Project Type**: CLI tool (local execution)

**Performance Goals**: Measure ID generation must add <100ms overhead; `export list` must respond in <1s regardless of run count; `export run` copy (JSON) must complete in <2s

**Constraints**: Must preserve backward compatibility — `export run` without runs falls back to full pipeline; existing `specmetrics-output.json` continues to be written

**Scale/Scope**: Designed for tens to low hundreds of run directories; no archiving/purging policy in v1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**:
- **I (Specification First)** — Measure command still consumes specifications as primary input; ID/export are orthogonal additions
- **V (Evidence First)** — Per-run persistence preserves traceability to exact specification state, config, and plugin versions
- **VII (Canonical Representation)** — Export reads canonical JSON from run directory, not framework-specific artifacts
- **VIII (Plugin-Oriented)** — `export list` reuses existing plugin discovery pattern; tabular CSV/XML normalization is lightweight and decoupled from CFM plugins
- **X (AI-Friendly by Design)** — Structured JSON per run + export output are machine-consumable
- **XI (Observability)** — Run directory with IDs creates an audit trail of all measurements
- **XIV (Layer Independence)** — Export layer reads persisted files without depending on pipeline internals

**Compliance Verifications**:
- [x] Specification First: The measure command consumes specs as primary input
- [x] Evidence First: Per-run persistence preserves traceability to the exact measurement context
- [x] Canonical Representation: Export reads canonical JSON, not framework-specific artifacts
- [x] Plugin-Oriented: CSV/XML conversion is decoupled from CFM plugins; `export list` uses existing patterns
- [x] Rule Externalization: Not engaged — no measurement policies are embedded
- [x] Layer Independence: Export layer reads persisted files only; CLI commands are interaction-layer concerns
- [x] Open by Default: JSON is an open standard; CSV and XML are widely supported formats

## Project Structure

### Documentation (this feature)

```text
specs/031-measure-id-export/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-interface.md # CLI command contracts
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
└── cli/
    ├── app.py                   # + measure --export, --format flags
    ├── export_commands.py       # + list subcommand; refactor run to read from runs/
    └── measure.py               # + measure ID generation, .specmetrics/runs/ persistence

specmetrics/
└── application/
    ├── models.py                # + MeasureOutput.id, .id_path fields
    └── orchestrator.py          # + save per-stage JSON to run directory

specmetrics/
└── plugins/
    └── exporter/
        └── orchestrator.py      # + read from run directory, tabular normalization for CSV/XML

tests/
├── cli/
│   ├── test_app.py              # + tests for --export, --format
│   ├── test_measure.py          # + tests for measure ID generation & persistence
│   └── test_export_commands.py  # + tests for export list & refactored export run
├── contract/
│   └── test_measure_output.py   # + tests for measure.id, measure.id_path in JSON
└── integration/
    └── test_export_run.py       # + integration test for export from run directory
```

**Structure Decision**: Single project (existing layout). Changes are confined to the CLI layer (`cli/`), application layer (`application/`), and exporter layer (`plugins/exporter/`). No new directories required beyond the existing structure.
