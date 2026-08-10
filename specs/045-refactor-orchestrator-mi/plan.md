# Implementation Plan: Refactor Pipeline Orchestrator for Maintainability

**Branch**: `045-refactor-orchestrator-mi` | **Date**: 2026-08-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/045-refactor-orchestrator-mi/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

The pipeline orchestrator module `specmetrics/application/orchestrator.py` (1,095 lines,
Maintainability Index `0.00`) blocks the release quality gate. This plan refactors it
into smaller cohesive units within the application layer so it scores MI **> 30** on the
project's radon-based gate, while preserving — byte-for-byte — every externally consumed
signature and behavior. No new features, metrics, or data entities are introduced; the
change is purely structural (FR-001..FR-006).

## Technical Context

**Language/Version**: Python 3.13 (venv), `from __future__ import annotations`

**Primary Dependencies**: structlog, Pydantic v2 (`~=2.7`, used by application models); Kernel classes (`PipelineEngine`, `PluginRegistry`, `HandlerRegistry`, `AdapterRegistry`, `PipelineContext`, `PipelineError`, `EventType`); missing: `typing`, `datetime`, `json`, `pathlib`, `collections.abc` from stdlib

**Storage**: N/A (persists transient JSON run artifacts to `<project>/.specmetrics/runs/<id>/*.json`; no database)

**Testing**: pytest (unit + integration), coverage `--cov-fail-under=85`, ruff + flake8 lint, radon/xenon/lizard complexity, jscpd duplication, mutatest, semgrep via `make quality-gate`

**Target Platform**: Linux local execution (CLI + MCP); library importable by external consumers

**Project Type**: library + CLI (Typer) + MCP server

**Performance Goals**: N/A for this refactor; no measurable behavior or throughput change (FR-002)

**Constraints**: Purely structural refactor (spec Assumptions); MUST NOT change public method signatures or observable results; MUST keep all existing tests passing unmodified (FR-006), and existing tests are the primary regression detection mechanism

**Scale/Scope**: Single module `specmetrics/application/orchestrator.py`; supporting NEW modules created only within `specmetrics/application/` (spec Assumption allows extraction to support the refactor); retention of `specmetrics/application/models.py`, `enums.py`, `metrics_json.py` untouched

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: Layer Independence (XIV), Canonical Representation (VII), Evolution Without Disruption (XIII), Plugin-Oriented Architecture (VIII), Open by Default (XII).

**Compliance Verifications**:
- [x] Specification First: Primary input is the feature specification (spec.md); the refactor is driven by requirements and success criteria, not code archaeology.
- [x] Evidence First: Design preserves all behavioral evidence; pre/post equivalence is validated against the existing test suite and save/read run artifacts (traceable outputs).
- [x] Canonical Representation: Refactor continues to operate on `PipelineContext`, `PipelineResult`, and the Canonical Functional Model through stable Kernel abstractions; no SDD-framework specifics introduced.
- [x] Plugin-Oriented: No new plugin surface is introduced (out of scope by spec); existing plugin discovery/load behavior is preserved unchanged.
- [x] Rule Externalization: No new measurement policies; the MI threshold lives in `scripts/complexity_metrics.py` and is untouched.
- [x] Layer Independence: The split units depend only on the orchestrator's existing dependencies (application models/enums + Kernel stable APIs); units do not reach into other layers' internals.
- [x] Open by Default: The public API contract remains documented and unchanged; new internal modules are normal modules under `specmetrics/application/`.

**Gate evaluation**: No violations. All engaged principles are complied with by design. No complexity justification required.

## Project Structure

### Documentation (this feature)

```text
specs/045-refactor-orchestrator-mi/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
specmetrics/
├── application/
│   ├── __init__.py
│   ├── config.py          # UNCHANGED
│   ├── enums.py           # UNCHANGED
│   ├── measure_id.py      # UNCHANGED
│   ├── metrics_json.py    # UNCHANGED
│   ├── models.py          # UNCHANGED
│   ├── orchestrator.py    # REFACTORED: thin PipelineOrchestrator entry point (public API preserved)
│   ├── stage_mapping.py   # NEW: event/name/handler maps, _stage_name_from_event, _resolve_event_order, _detect_framework
│   ├── truncation.py      # NEW: _truncate_text, _truncate_entities helpers
│   ├── artifact_persistence.py  # NEW: save_run_artifacts, read_run_artifacts, _serialize_stage_data
│   ├── entity_builders.py # NEW: _build_stage_entities + _entities_for_* + _coerce_element_*
│   ├── metric_builders.py # NEW: _build_metric_results, _extract_measurement, _build_metric_entry, _metric_breakdown, _metric_warnings
│   ├── stage_builders.py  # NEW: _build_stage_results, _build_stage_details, _detail_count, _count_*, _stage_timing, _status_for_kernel, _duration_seconds, _entities_for_stage
│   └── export_writer.py   # NEW: _handle_export, _handle_structured_export, _write_json_output, _build_output_errors, _get_llm_info

tests/
├── unit/application/test_orchestrator.py   # KEPT, unmodified (regression)
└── application/test_orchestrator.py        # KEPT, unmodified (regression)
```

**Structure Decision**: Single `specmetrics/application/` package, one public entry module
(`orchestrator.py`) plus a set of small single-responsibility collaborators. Each module
maps to one of the FR-003 responsibilities: entity building (`entity_builders.py`), metric
assembly (`metric_builders.py`), stage/result assembly (`stage_builders.py`), artifact
persistence (`artifact_persistence.py`), structured export (`export_writer.py`), shared
stage/event mapping (`stage_mapping.py`), and reusable truncation helpers (`truncation.py`).
Constants that are imported by external consumers and helper logic that is heavily coupled
to multiple responsibilities are split into their own modules to keep every unit small and
low-complexity. `models.py`, `enums.py`, `metrics_json.py` stay untouched.

## Complexity Tracking

> No Constitution Check violations to justify; this table intentionally left empty.