# Contract: Pipeline Orchestrator Public API

**Feature**: [spec.md](../spec.md) | **Phase**: 1 | **Date**: 2026-08-04
**Module**: `specmetrics/application/orchestrator.py`

## Purpose

Defines the externally consumed interface of the pipeline orchestrator. This contract is
**frozen** for this refactor: FR-002, FR-004 and US-3 require these signatures and behaviors
to remain identical before and after restructuring. CLI (`specmetrics/cli/app.py`,
`cli/measure.py`, `cli/plugins.py`, `cli/export_commands.py`) and MCP
(`specmetrics/mcp/tools/measure.py`, `mcp/tools/export.py`) depend on it.

## Contract Version

`v1` — unchanged by this feature. Changes require a new contract version + migration review.

## Symbols

### Class `PipelineOrchestrator`

Constructor:
- `PipelineOrchestrator()` — initializes empty registries; no arguments.

Public methods (MUST keep exact signatures):

| Signature | Behavior (unchanged) |
|-----------|----------------------|
| `set_config_system(self, config_system: ConfigurationSystem) -> None` | Sets the configuration system used for schema registration, config load, and LLM info. |
| `discover_plugins(self, metrics_filter: list[str] \| None = None) -> None` | Loads plugins into the registry and installs handlers; registers plugin config schemas when a config system is present. Optional-component load failures warn-and-continue (FR-005). |
| `list_plugins(self) -> list[PluginInfo]` | Returns metadata for all discovered plugins. |
| `get_version_info(self) -> VersionInfo` | Returns platform, Python, and plugin versions. |
| `execute(self, request: PipelineRequest) -> PipelineResult` | Runs the measurement pipeline and returns the structured result. |

`execute` result guarantees (FR-005):
- Missing/invalid `request.project_path` → `PipelineResult(status=FAILED, error="Project path not found: <path>")`, no plugins discovered, no engine run.
- Kernel raises `PipelineError` → `PipelineResult(status=FAILED, error=str(exc), project_path=..., duration_seconds=elapsed)`.
- Config system load failure → tolerated (warning) and pipeline proceeds without config.
- `has_failures` (any stage FAILED) → `PipelineResult.status = FAILED`, else `SUCCESS`.

### Module-level functions (MUST keep exact signatures)

| Signature | Behavior (unchanged) |
|-----------|----------------------|
| `save_run_artifacts(project_path: Path, measure_id: str, result: PipelineResult, max_entities_per_stage: int = 5000) -> Path` | Persists `metadata.json` and one `<stage>.json` per stage under `<project_path>/.specmetrics/runs/<measure_id>/`; returns the run directory. |
| `read_run_artifacts(run_dir: Path) -> dict` | Loads saved artifacts into `{metadata, <stage>: [...]}`; skips `metadata.json` and `metrics.json` from stage iteration. |

### Private delegating methods (MUST keep for test compatibility — FR-006)

Existing tests call these on an `orch` instance; they MUST remain on the class as thin
delegators (logic lives in the extracted units):

- `orch._build_metric_results(ctx, metrics_filter) -> list[MetricOutputItem]`
  (referenced `tests/unit/application/test_orchestrator.py:68,81,89`)
- `orch._write_json_output(request, ctx, export_dir, metric_results, stage_details, output_errors) -> Path`
  (referenced `:111`)

## Non-Goals / Out of Scope

- No changes to `models.py`, `enums.py`, or any Kernel class.
- No public signature additions or removals.
- No changes to plugin discovery entry points.