# Data Model: Refactor Pipeline Orchestrator for Maintainability

**Feature**: [spec.md](./spec.md) | **Phase**: 1 (Design & Contracts) | **Date**: 2026-08-04

## Scope Note

The feature specification explicitly states **no new data entities are introduced**
(spec "Key Entities" section). This refactor is purely structural. The orchestrator
consumes existing application-level models; this document records those existing
entities (for reference, untouched by the refactor) and the **internal unit boundaries**
of the refactored orchestrator, which are code-module responsibilities, not data
entities.

## Existing Entities (UNCHANGED)

Defined in `specmetrics/application/models.py` and `specmetrics/application/enums.py`.
The refactor must not alter these definitions.

### Entity: `PipelineRequest`
| Field | Type | Notes |
|-------|------|-------|
| `project_path` | `Path` | MUST exist before execution; missing path → FAILED result |
| `stages` | `list[StageName] \| None` | Overrides stage order when set |
| `from_stage` | `StageName \| None` | Partial run start point |
| `metrics_filter` | `list[str] \| None` | Restricts metric computation |
| `output_format` | `OutputFormat` | `NONE`/`JSON`/`CSV`/`XML` |
| `output_path` | `Path \| None` | Export destination override |
| `measure_id` | `str` | Run identifier for metadata |
| `llm_rpm_limit` | `int \| None` | LLM gateway rate limit |

### Entity: `PipelineResult`
| Field | Type | Notes |
|-------|------|-------|
| `status` | `PipelineStatus` | `SUCCESS`/`FAILED`; FAILED when any stage FAILED |
| `project_path` | `Path` | Echoed request path |
| `run_id` | `str` | Kernel `execution_id` |
| `stages_executed` | `list[StageResult]` | Per-stage status/duration/entities_found |
| `stage_details` | `list[StageOutputItem]` | Export-stage detail rows |
| `stage_entities` | `dict[str, list[dict]]` | Truncated entity payloads per stage |
| `measurement` | `MeasurementResult \| None` | Primary FPA summary |
| `metric_results` | `list[MetricOutputItem]` | Per-metric totals |
| `output_errors` | `list[ErrorOutputItem]` | Diagnostics errors |
| `export_path` | `Path \| None` | Written output file |
| `canonical_model` | `CanonicalFunctionalModel \| None` | CFM from pipeline context |
| `llm_provider` / `llm_model` | `str` | LLM info |
| `duration_seconds` | `float` | Wall-clock run duration |
| `measurement_result_raw` | `dict[str, Any]` | Raw kernel measurement map |
| `llm_call_stats` | `Any` | Gateway summary |

### Supporting entities
- `StageResult`, `StageOutputItem`, `MetricOutputItem`, `ErrorOutputItem`, `PluginInfo`,
  `VersionInfo`, `MeasurementResult` — output DTOs assembled by the orchestrator.
- `StageName`, `StageExecutionStatus`, `PipelineStatus`, `OutputFormat` — enums.

## Refactor Unit Boundaries (code modules, NOT data entities)

These are the cohesive units extracted from `orchestrator.py` (FR-003). Each is a
single-responsibility module under `specmetrics/application/`.

| Unit | Responsibility | Key operations |
|------|---------------|----------------|
| `orchestrator.py` | Thin public entry point + pipeline run + result assembly wiring | `execute`, `discover_plugins`, `list_plugins`, `get_version_info`, `set_config_system`; thin delegating wrappers `_build_metric_results`, `_write_json_output` (test contract, see [research.md](./research.md)) |
| `stage_mapping.py` | Stage name ↔ event ↔ handler-name mapping and event-order resolution | `_STAGE_NAME_TO_EVENT`, `_STAGE_NAME_TO_HANDLER_NAMES`, `_stage_name_from_event`, `_resolve_event_order`, `_detect_framework` |
| `truncation.py` | Text/entity truncation helpers | `_truncate_text`, `_truncate_entities` |
| `artifact_persistence.py` | Run-folder artifact persistence | `save_run_artifacts`, `read_run_artifacts`, `_serialize_stage_data` |
| `entity_builders.py` | Per-stage entity payload builders | `_build_stage_entities`, `_entities_for_{discover,extract,graph,csm,cfm,rule,measure,export}`, `_coerce_element_{dict,obj,evidence}` |
| `metric_builders.py` | Metric & measurement assembly | `_build_metric_results`, `_build_metric_entry`, `_metric_breakdown`, `_metric_warnings`, `_extract_measurement` |
| `stage_builders.py` | Stage result/detail rows and counting | `_build_stage_results`, `_build_stage_details`, `_detail_count`, `_count_{discover,extract,graph,model_elements,measure}`, `_stage_timing`, `_status_for_kernel`, `_duration_seconds`, `_entities_for_stage` |
| `export_writer.py` | Output/structured export and error assembly | `_handle_export`, `_handle_structured_export`, `_write_json_output`, `_build_output_errors`, `_get_llm_info` |

### Dependency rules (layer independence, XIV)
- Units depend ONLY on: `specmetrics/application/models.py`, `specmetrics/application/enums.py`,
  `specmetrics/kernel/*` stable classes already imported by the orchestrator today, and each other
  as documented above.
- No unit may import from `specmetrics/cli/*`, `specmetrics/mcp/*`, or any SDD-framework adapter.
- `stage_mapping.py` and `truncation.py` have no dependencies (pure helpers).

## State Transitions

Not applicable — no new state machine. Existing behavior preserved: `PipelineResult.status`
is `FAILED` if any stage `StageExecutionStatus == FAILED`, else `SUCCESS`; project-path
validation failure returns an early `FAILED` result; `PipelineError` from the Kernel returns
a `FAILED` result with the error string (FR-005).

## Validation Rules (existing, preserved)

- Truncation: `_TRUNCATE_TEXT_LENGTH = 200`; per-stage entity cap default `5000`,
  configurable via `run_artifacts.max_entities_per_stage` (read from config provider).
- Entity coercion: entries with no `id`/`type`/`content` are dropped.
- MI gate (not data validation): worst radon MI `< 30` blocks the quality gate — target
  of this refactor, evaluated by `scripts/complexity_metrics.py`.
