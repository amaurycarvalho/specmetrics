# Implementation Plan: Measure Metric Filtering & JSON Output

**Branch**: `030-measure-metric-filter` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/030-measure-metric-filter/spec.md`

## Summary

Add an optional positional argument to `specmetrics measure` that accepts metric identifiers (`all|bcp|fpa|sfp|snap|sp|tshirt|tp|cp`) to filter which measurements execute. Change the output file from `specmetrics-output.text` to `specmetrics-output.json` with a structured schema containing measure metadata, per-metric results, stages, and errors. Update text output to show all selected metric totals.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Typer (CLI argument parsing), Pydantic v2 (JSON output models)

**Storage**: `.specmetrics/output/specmetrics-output.json` (JSON file)

**Testing**: pytest

**Target Platform**: Linux, macOS, Windows (CLI tool)

**Project Type**: CLI tool within existing Typer CLI

**Performance Goals**: Metric parsing and validation <100ms; filtered execution must skip unselected metrics without overhead

**Constraints**: Must use existing entry-point-based plugin discovery for metric identifiers; must not modify individual measurement plugin internals (Layer Independence XIV); the `specmetrics-output.text` file is replaced by `specmetrics-output.json`

**Scale/Scope**: Up to 8 metrics in a single command; metric list passed as comma-separated CLI argument

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: Specification First (I), Canonical Representation (VII), Plugin-Oriented (VIII), AI-Friendly by Design (X), Observability as a Native Capability (XI), Layer Independence (XIV)

**Compliance Verifications**:
- [x] Specification First (I): The measure command continues to consume specifications as input; filtering does not alter this.
- [x] Evidence First (V): The JSON output schema includes errors array that preserves traceability of failures; measurement results still carry evidence references via each metric plugin.
- [x] Canonical Representation (VII): Metric filtering operates at the orchestration layer, selecting which plugins to invoke — it does not bypass or modify the canonical model.
- [x] Plugin-Oriented (VIII): Metric identifiers map to registered plugin entry points. Filtering selects plugins to invoke rather than hardcoding metric logic.
- [x] Rule Externalization (IX): Filtering does not affect Rule Pack application — rules continue to be externalized.
- [x] Layer Independence (XIV): Filtering is implemented at the CLI/orchestration level. No measurement plugin internals are modified.
- [x] Open by Default (XII): JSON output format is documented and machine-readable.

Gate status: **PASS** — No violations detected. All engaged principles are satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/030-measure-metric-filter/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── measure-cli-interface.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
├── cli/
│   ├── app.py           # Add metrics positional argument to measure command
│   └── measure.py       # Parse metrics arg, pass to PipelineRequest, new JSON output
├── application/
│   ├── models.py        # Add metrics_filter to PipelineRequest; expand MeasurementResult/PipelineResult
│   ├── enums.py         # No changes needed (metric identifiers are strings)
│   └── orchestrator.py  # Filter measurement plugins by metrics_filter; write JSON output file
├── cli/
│   └── formatters.py    # Show all selected metrics in text output; JSON formatter
└── tests/
    ├── cli/
    │   ├── test_app.py           # Test new measure argument parsing
    │   └── test_measure.py       # Test metric filtering logic
    ├── unit/
    │   └── application/
    │       └── test_orchestrator.py  # Test metric filter application
    ├── integration/
    │   └── test_metric_filter_pipeline.py  # End-to-end filtered measurement
    └── contract/
        └── test_measure_output.py  # JSON output schema contract tests
```

**Structure Decision**: Metric filtering is implemented at the CLI/orchestration boundary. The CLI parses and validates the metric argument, then passes it to the orchestrator via `PipelineRequest`. The orchestrator uses the filter to decide which measurement plugins to invoke. Output formatting changes are confined to `formatters.py`. This keeps all changes aligned with the existing Layered Architecture: CLI → Application → Kernel.

## Complexity Tracking

> No complexity violations detected. Gate status: PASS.
