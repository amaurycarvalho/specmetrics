# Implementation Plan: Measure Metrics Breakdown

**Branch**: `036-measure-metrics-breakdown` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/036-measure-metrics-breakdown/spec.md`

## Summary

Generate a `metrics.json` file inside the run directory (`runs/<measure_id>/`) containing per-entity score breakdowns for every metric executed. The file uses a uniform schema — all metric types share identical top-level and entity-level keys — with metric-specific detail nested in optional `metadata` objects. This serializes entity data that already exists in each handler's measurement result objects but is currently discarded after the `handle()` method returns.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Pydantic v2 (uniform schema models), Typer (CLI), structlog (logging), json stdlib (serialization)

**Storage**: JSON file written to `.specmetrics/runs/<measure_id>/metrics.json`

**Testing**: pytest

**Target Platform**: Linux (CLI)

**Project Type**: CLI tool extension

**Performance Goals**: <200ms additional overhead for 500 entities across all metrics; linear scaling for larger counts

**Constraints**: UTF-8 encoding, pretty-printed JSON (2-space indent), no truncation of entity lists

**Scale/Scope**: Up to thousands of entities per run; 8 metrics (fpa, sfp, snap, bcp, storypoints, token_points, cognitive_points, tshirt); ~40-50 existing payload keys in `measurement_result` dict

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**:
- Principle IV (LLM-Assisted, Deterministic Results): metrics.json records output of deterministic engines
- Principle V (Evidence First): entity `id` preserves traceability to canonical model elements
- Principle VI (Explainability by Design): per-entity scores make measurements auditable
- Principle VII (Canonical Representation): uniform schema operates on normalized outputs
- Principle XI (Observability as a Native Capability): metrics.json is structured telemetry
- Principle XIV (Layer Independence): reads from measurement layer, writes to publication layer

**Compliance Verifications**:
- [x] Specification First: Feature consumes measurement results derived from software specifications
- [x] Evidence First: Entity `id` (compound URI) preserves the chain to CFM/CSM elements
- [x] Canonical Representation: Uniform schema normalizes metric-specific details into metadata
- [x] Plugin-Oriented: New `MetricsJsonBuilder` is an application-layer module; handlers are extended in-place (not new plugins)
- [x] Rule Externalization: N/A — this feature serializes already-computed results; no new counting rules
- [x] Layer Independence: Builder reads from `measurement_result` dict (published by handlers via pipeline context); does not bypass architectural boundaries
- [x] Open by Default: JSON schema is documented in data-model.md; file is human-readable

## Project Structure

### Documentation (this feature)

```text
specs/036-measure-metrics-breakdown/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
specmetrics/
├── application/
│   ├── models.py              # Add MetricBreakdownEntry, EntityScore models
│   ├── metrics_json.py        # NEW: MetricsJsonBuilder + save_metrics_json()
│   └── orchestrator.py        # Expose measurement_result_raw for builder access
├── plugins/measurement/
│   ├── fpa/plugin.py          # Add fpa_entities to payload
│   ├── sfp/plugin.py          # Add sfp_entities to payload
│   ├── snap/plugin.py         # Add snap_entities to payload
│   ├── bcp/plugin.py          # Add bcp_entities to payload
│   ├── storypoints/plugin.py  # Add storypoints_entities to payload
│   ├── token_points/plugin.py # Add token_entities to payload
│   ├── cognitive_points/plugin.py # Add cognitive_entities to payload
│   └── tshirt/plugin.py       # Add tshirt_entities to payload
├── cli/
│   └── measure.py             # Call save_metrics_json() after save_run_artifacts()
└── tests/
    └── test_metrics_json.py   # NEW: unit + integration tests
```

**Structure Decision**: No new directories needed. The feature extends existing handler payloads (one additional key per handler) and adds a single new application module (`metrics_json.py`). Tests go into existing `tests/` directory.

## Complexity Tracking

> No constitution violations to justify. The feature uses existing extension points (handler payloads) and adds a lightweight serialization layer without introducing new architectural patterns.

## Design Decisions

### 1. Per-Entity Data Source

**Finding**: Handlers create rich result objects with entity lists (`MeasuredFunction`, `FunctionalWorkItem`, `TokenContribution`, etc.) but discard them after aggregating scalars into the `measurement_result` dict. Entity lists are NOT stored anywhere accessible after pipeline execution.

**Decision**: Modify each handler to include a serialized entity list in its `measurement_result` payload under a metric-scoped key (e.g., `fpa_entities`). Each entity is serialized as a flat dict with canonical `id`, `name`, `type`, `score`, and metric-specific `metadata`. This approach:
- Reuses the existing `merge_stage_output` pattern
- Requires no changes to `PipelineContext` (still a frozen dataclass with dict merge)
- Keeps entity data scoped by metric key for easy consumption

### 2. Uniform Schema Builder

**Decision**: Create `specmetrics/application/metrics_json.py` with:
- Pydantic models (`MetricBreakdownEntry`, `EntityScore`) matching the spec's Key Entities
- A `MetricsJsonBuilder` class that reads from the `measurement_result` dict and maps each metric's raw entity dicts to the uniform `EntityScore` model
- A `save_metrics_json()` function that serializes and writes `metrics.json`

### 3. Canonical Type Mapping

Each metric maps its internal entity types to canonical types as follows:

| Metric | Internal Types | Canonical `type` |
|--------|---------------|------------------|
| FPA | ILF, EIF | `data_group` |
| FPA | EI, EO, EQ | `operation` |
| SFP | logical_function | `data_group` |
| SFP | functional_process | `functional_process` |
| SNAP | presentation | `specification_activity` |
| SNAP | data_operations | `operation` |
| SNAP | operational_capabilities | `functional_process` |
| SNAP | technical_interaction | `relationship` |
| BCP | (functional processes) | `functional_process` |
| Story Points | (functional processes) | `functional_process` |
| Token Points | (varies per element) | Map element_type directly (already canonical) |
| Cognitive Points | (varies per element) | Map element_type directly (already canonical) |
| TShirt | (functional processes) | `functional_process` |

### 4. Score Field Semantics

| Metric | Entity `score` | Source field |
|--------|---------------|--------------|
| FPA | UFP weight | `ufp_weight` |
| SFP | Contribution | `contribution` |
| SNAP | Contribution | `contribution` |
| BCP | BCP score | `bcp_score` |
| Story Points | Normalized value | `normalized_value` |
| Token Points | Partial score | `partial_score` |
| Cognitive Points | Partial score | `partial_score` |
| TShirt | Story point value | `story_point_value` |
