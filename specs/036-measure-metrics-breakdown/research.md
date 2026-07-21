# Research: Measure Metrics Breakdown

**Feature**: 036-measure-metrics-breakdown
**Date**: 2026-07-21

## Research Task 1: How to Access Per-Entity Data After Pipeline Execution

### Finding

All eight measurement handlers create rich result objects with entity lists during `handle()`, but only extract aggregated scalars into the `measurement_result` payload. The entity lists are local variables that go out of scope when `handle()` returns.

**Evidence**:
- FPA handler (`plugins/measurement/fpa/plugin.py:111-122`): Creates `FPAMeasurementResult` with `measured_functions: list[MeasuredFunction]`. Payload only contains `fpa_total_function_points`, `fpa_breakdown`, etc.
- Story Points handler (`plugins/measurement/storypoints/plugin.py:87-98`): Creates `StoryPointMeasurementResult` with `items: list[FunctionalWorkItem]`. Payload only contains `storypoints_total_story_points`, `storypoints_estimated_items` (int count, not list).
- Token Points handler (`plugins/measurement/token_points/plugin.py:62-80`): Creates `TokenPointsMeasurement` with `specification_cost.contributions` and `code_generation_cost.contributions`. Payload only contains `token_total_score`, `token_element_counts`, etc.
- BCP handler (`plugins/measurement/bcp/plugin.py:81-91`): Creates `BCPMeasurementResult` with `items: list[BCPWorkItem]`. Payload only contains `bcp_total_bcp`, `bcp_measured_items`.
- Other handlers (SFP, SNAP, Cognitive Points, TShirt) follow the same pattern.

**TShirt gap confirmation**: The TShirt handler attempts to read `measurement_result.get("items")` or `measurement_result.get("estimated_items")` from Story Points data (`tshirt/plugin.py:190-197`), but these keys ARE NEVER WRITTEN by the Story Points handler. This confirms the entity-list gap is structural.

### Decision

**Modify each handler to emit entity lists in its payload.** Each handler will add a single new key (e.g., `fpa_entities`, `storypoints_entities`) containing a list of serialized entity dicts. This approach:
1. Uses the existing `merge_stage_output` mechanism — no kernel changes
2. Keeps entity data scoped per metric via distinct keys
3. Avoids storing full Pydantic model objects in the context (serializes to plain dicts)

### Alternatives Considered

- **Store result objects on handler instances**: Rejected — handlers are singletons registered at startup; storing state would be thread-unsafe and conflict between runs.
- **Add new field to PipelineContext**: Rejected — `PipelineContext` is a frozen dataclass; changing it requires modifying kernel code.
- **Extract entities from CFM post-measurement**: Rejected — requires re-running classification logic, violates single-responsibility, and may produce different results than what the engine computed.
- **Use a side-channel registry**: Rejected — adds complexity without benefit; the payload dict approach is the simplest.

---

## Research Task 2: Canonical Type Mapping Strategy

### Finding

The spec defines a fixed canonical vocabulary of 14 entity types. Each metric's internal element types must be mapped to these canonical types. The mapping is straightforward for most metrics:

**FPA**: `ILF` and `EIF` are sub-types of `data_group`. `EI`, `EO`, and `EQ` are sub-types of `operation`. The metric-specific sub-type is preserved in `metadata.function_type`.

**SFP**: `functional_process` maps directly to canonical `functional_process`. `logical_function` maps to `data_group`.

**SNAP**: Categories map based on their semantic domain: `presentation` → `specification_activity`, `data_operations` → `operation`, `operational_capabilities` → `functional_process`, `technical_interaction` → `relationship`.

**BCP, Story Points, TShirt**: All operate on `functional_process` entities exclusively.

**Token Points and Cognitive Points**: These already use element type names that overlap heavily with the canonical set (e.g., `specification_activity`, `business_rule`, `operation`, `data_group`, `actor`, `relationship`). Their internal element types can be passed through with minimal normalization.

### Decision

**Metric-specific canonical type mapping functions.** The `MetricsJsonBuilder` will include a mapping table that converts each metric's internal type strings to canonical types. This is implemented as a static dictionary in `metrics_json.py`.

### Alternatives Considered

- **Make handlers emit canonical types directly**: Rejected — handlers should emit their native types; mapping is a builder responsibility.
- **Infer canonical type from element category in CFM**: Rejected — not all entities have a direct CFM counterpart (e.g., SNAP items are synthesized).

---

## Research Task 3: Integration Point in Pipeline

### Finding

The `run_measure()` function in `cli/measure.py` (lines 122-226) is the orchestration entry point. After `orchestrator.execute(request)` returns a `PipelineResult`, `save_run_artifacts()` writes stage JSON files to the run directory. This is the natural point to inject `metrics.json` generation.

The `PipelineResult` already carries `metric_results: list[MetricOutputItem]` with scalar totals per metric. For entity data, the builder needs the raw `measurement_result` dict from the pipeline context.

Currently, `PipelineResult` does not expose the raw `measurement_result` dict. The orchestrator's `execute()` method populates `result.metric_results` and `result.measurement` (FPA-only summary) from the context, but the raw dict is discarded.

### Decision

**Expose the raw `measurement_result` dict on `PipelineResult`.** Add a `measurement_result_raw: dict` field to `PipelineResult`. The orchestrator populates it from `ctx.measurement_result`. The `MetricsJsonBuilder` reads from this field to access entity lists by their scoped keys.

The `save_metrics_json()` function will be called from `run_measure()` immediately after `save_run_artifacts()`, using the same project path, measure_id, and result object.

### Alternatives Considered

- **Access PipelineContext directly after execution**: Rejected — `PipelineContext` is consumed by the orchestrator and not returned to the caller.
- **Integrate into save_run_artifacts()**: Rejected — keeps concerns separate; `metrics.json` has a different schema than stage artifact files and deserves its own function.
- **Insert as a new pipeline stage**: Rejected — the builder is a post-pipeline serialization step, not a measurement engine with deterministic counting rules.

---

## Research Task 4: Metadata Content for Each Metric

### Finding

Each metric has a unique set of auxiliary data that should appear in `metadata` at the metric and entity levels. This data already exists in the handler's result objects and can be included in the entity payload.

### Decision

**Entity metadata per metric:**

| Metric | Entity `metadata` fields |
|--------|-------------------------|
| FPA | `function_type`, `complexity`, `det_count`, `ret_count` (data functions), `ftr_count` (transactions) |
| SFP | `component_type` |
| SNAP | `category_id`, `cfm_semantic_marker` |
| BCP | `component_breakdown`, `generated_story` |
| Story Points | `raw_score`, `normalized_value`, `factor_breakdown`, `applied_rules` |
| Token Points | `applied_weight`, `model_source`, `element_type` |
| Cognitive Points | `bloom_level`, `cognitive_weight`, `model_source`, `element_type` |
| TShirt | `tshirt_size`, `mapping_rule` |

**Metric-level metadata per metric:**

| Metric | Metric `metadata` fields |
|--------|--------------------------|
| FPA | `method: "ifpug"`, `vaf` |
| SFP | `method: "simplified"`, `fp_contribution`, `lf_contribution` |
| SNAP | `categories` (list of category snapshots) |
| BCP | `method`, `provider`, `sdk_version` |
| Story Points | `scale: "fibonacci"`, `method` |
| Token Points | `calibration_version` |
| Cognitive Points | `calibration_version`, `raw_score`, `fibonacci_normalization` |
| TShirt | `scale`, `mapping` (XS=1, ..., XXL=100) |

### Alternatives Considered

- **Put all metadata in a single metric-level object**: Rejected — entities in dashboards need per-entity metadata for filtering and grouping.
- **Flatten all metadata into entity fields**: Rejected — violates uniform schema requirement (FR-008); metric-specific fields must be in metadata.
