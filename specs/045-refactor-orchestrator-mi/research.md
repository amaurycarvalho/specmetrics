# Research: Refactor Pipeline Orchestrator for Maintainability

**Feature**: [spec.md](./spec.md) | **Phase**: 0 (Outline & Research) | **Date**: 2026-08-04

## Research Tasks

| ID | Question / Unknown | Task |
|----|--------------------|------|
| R-01 | How is Maintainability Index measured and what threshold is blocking? | Inspect `scripts/complexity_metrics.py` and `Makefile` quality-gate wiring. |
| R-02 | What is the current orchestrator MI and what drives it down? | Run `radon mi -s` and `radon cc -a -s` on `specmetrics/application/orchestrator.py`. |
| R-03 | What is the externally consumed public contract of the orchestrator? | Grep imports of `specmetrics.application.orchestrator` across CLI, MCP, and tests. |
| R-04 | How should a large orchestrator be decomposed to raise MI without behavior change? | Best-practice research on single-responsibility extraction for Python orchestrators/coordinators. |
| R-05 | What validation proves behavioral equivalence? | Review existing unit/integration tests for pipeline execution, run artifacts, and export output. |

## Findings & Decisions

### R-01 — Maintainability tooling and gate contract

- **Decision**: The project's automated maintainability measurement is `radon mi` (script `scripts/complexity_metrics.py`), executed by `make complexity` within `make quality-gate`. A module whose **worst** (minimum) MI score is `< 30.0` is a **blocking** gate failure (exit 1); `30 <= worst < 70` is a warning (exit 0); `>= 70` passes. An empty/unparseable MI result is treated as blocking (fail-loud).
- **Rationale**: Direct inspection of `scripts/complexity_metrics.py:79-92` shows `worst = min(scores)` and `gate_failed = True` only when `worst < MI_BLOCKING` (30.0). This is the "established quality-gate contract" referenced in the spec Assumptions.
- **Alternatives considered**: `radon cc`/`xenon`/`lizard` complexity gates — considered but rejected as the MI source: they gate cyclomatic complexity, not maintainability index, and are separate checks in the Makefile.

### R-02 — Current orchestrator score and root cause

- **Decision**: `specmetrics/application/orchestrator.py` currently reports MI `0.00` (grade C), which is below the 30 blocking threshold.
- **Rationale**: `radon mi -s specmetrics/application/orchestrator.py` → `C (0.00)`. The module is 1,095 lines containing 49 blocks (classes/functions/methods); the class `PipelineOrchestrator` alone hosts 40+ methods including `execute` (CCN B=10), `discover_plugins` (B=8), `_build_stage_results` (B=7), `_build_stage_details` (B=7), `_handle_structured_export` (B=7). MI is a function of per-module volume/complexity, so the single oversized module guarantees the low score.
- **Alternatives considered**: Adding `# noqa`/radon exclude pragmas — rejected as gate-gaming; the spec demands a real structural refactor (FR-003).

### R-03 — Public contract to preserve

- **Decision**: The externally consumed symbols from `specmetrics.application.orchestrator` are:
  - `PipelineOrchestrator` class with methods `__init__`, `set_config_system(config_system)`, `discover_plugins(metrics_filter=None)`, `list_plugins()`, `get_version_info()`, `execute(request)`.
  - Module-level functions `save_run_artifacts(project_path, measure_id, result, max_entities_per_stage=5000)` and `read_run_artifacts(run_dir)`.
- **Rationale**: Imports confirmed in `specmetrics/cli/app.py:239`, `specmetrics/cli/measure.py:15-68`, `specmetrics/cli/export_commands.py:16-18`, `specmetrics/cli/plugins.py:9`, `specmetrics/mcp/tools/measure.py:12`, `specmetrics/mcp/tools/export.py:13`. These are the "externally exposed signatures" the spec requires to remain unchanged (US-3 / FR-004).
- **Alternatives considered**: Renaming or consolidating entry points — rejected; spec forbids signature changes.

### R-04 — Decomposition strategy to raise MI

- **Decision**: Extract each FR-003 responsibility into a dedicated module in `specmetrics/application/`, keeping `orchestrator.py` as a thin coordinator that only wires collaborators and preserves the public signatures. Proposed units:
  1. `stage_mapping.py` — `_STAGE_NAME_TO_EVENT`, `_STAGE_NAME_TO_HANDLER_NAMES`, `_stage_name_from_event`, `_resolve_event_order`, `_detect_framework`.
  2. `truncation.py` — `_truncate_text`, `_truncate_entities`.
  3. `artifact_persistence.py` — `save_run_artifacts`, `read_run_artifacts`, `_serialize_stage_data`.
  4. `entity_builders.py` — `_build_stage_entities` + `_entities_for_{discover,extract,graph,csm,cfm,rule,measure,export}` + `_coerce_element_*`.
  5. `metric_builders.py` — `_build_metric_results`, `_build_metric_entry`, `_metric_breakdown`, `_metric_warnings`, `_extract_measurement`.
  6. `stage_builders.py` — `_build_stage_results`, `_build_stage_details`, `_detail_count`, `_count_*`, `_stage_timing`, `_status_for_kernel`, `_duration_seconds`, `_entities_for_stage`.
  7. `export_writer.py` — `_handle_export`, `_handle_structured_export`, `_write_json_output`, `_build_output_errors`, `_get_llm_info`.
- **Rationale**: Single-responsibility modules reduce per-module SLOC/CCN so each scores well above the MI floor; `execute` keeps orchestration-only logic (request validation, config load, engine run, result assembly order) while delegating building to the units. This follows the established practice for coordinator refactors: separate "do the work" from "assemble the answer."
- **Alternatives considered**:
  - One flat helper module — rejected: still large, low cohesion.
  - Composition class (`ResultAssembler` with injected builders) — viable but adds indirection beyond need; plain module-level functions with explicit params keep diff smaller and preserve the existing test surface that reaches private methods. Note: if existing tests import `PipelineOrchestrator._private_*` directly, those tests are NOT to be modified (FR-006), so `orchestrator.py` must keep thin delegating stubs or the tests must only exercise public behavior — to be confirmed in Phase 2 tasking; default assumption is public-behavior-only tests.

### R-05 — Behavioral equivalence validation

- **Decision**: Rely on the existing unmodified test suite (`make test`, 85% coverage gate) plus the run-artifact persistence round-trip as the equivalence oracle. Validation scenarios are captured in `quickstart.md`.
- **Rationale**: US-2 acceptance scenarios require identical pipeline results; existing integration tests (`tests/integration/test_pipeline_execution.py`, exporter tests, `tests/application/test_orchestrator.py`) already exercise full pipeline execution and output assembly. `save_run_artifacts`/`read_run_artifacts` JSON gives a byte-comparable artifact to diff before/after.
- **Alternatives considered**: Snapshot-based golden files — rejected as unnecessary; existing assertions + a manual before/after artifact diff on a sample project satisfy SC-003/SC-004 without adding maintenance burden.

## Consolidated Decisions

| Decision | Choice |
|----------|--------|
| MI measurement | radon `mi`, worst-score `< 30` = blocking (per `scripts/complexity_metrics.py`) |
| Refactor mechanism | Extract single-responsibility modules under `specmetrics/application/`; thin orchestrator entry point |
| Public API | Unchanged: `PipelineOrchestrator` methods + `save_run_artifacts` + `read_run_artifacts` |
| Equivalence proof | Unmodified existing test suite + before/after run-artifact diff on a sample project |
| Scope guard | Only `orchestrator.py` restructured; new modules only under `specmetrics/application/`; no behavior changes |

## Open Items

- None — all unknowns resolved. Confirmatory finding raised during research and closed here: existing tests reach two private methods on `PipelineOrchestrator` directly — `orch._build_metric_results(...)` (`tests/unit/application/test_orchestrator.py:68,81,89`) and `orch._write_json_output(...)` (`:111`). Because FR-006 forbids modifying tests, `orchestrator.py` MUST keep thin delegating wrappers named `_build_metric_results` and `_write_json_output` that forward to the extracted `metric_builders.py` and `export_writer.py` units. These wrappers remain a few lines / low CCN and do not reintroduce the MI problem. Also note `tests/unit/test_truncation.py` and `tests/unit/test_serialize_stage_data.py` vendor their own copies of `_truncate_*`/`_serialize_stage_data`; they are independent regression tests and need no change. No spec-level clarification is required.
