# Data Model: Story Points Improvements

**Feature**: 040-story-points-improvements  
**Date**: 2026-07-21

## Entity Overview

```
StoryPointsCalibrationProfile (1) ──► StoryPointMeasurementResult (1)
                                           │
                                           ├── specification_effort_total: float
                                           ├── implementation_effort_total: float
                                           ├── content_multiplier: float
                                           ├── content_tokens_by_type: dict
                                           │
                                           └── items: list[WorkItem] (*)
                                                    │
                                                    ├── element_type: str
                                                    ├── raw_score: float
                                                    ├── normalized_value: int
                                                    ├── structural_score: float
                                                    ├── content_tokens: int
                                                    ├── content_score: float
                                                    ├── factor_breakdown: dict (FPs only)
                                                    └── evidence_refs: list[EvidenceRef]
```

## Core Entities

### WorkItem (renamed from FunctionalWorkItem)

Represents the estimation result for a single specification element.

| Field | Type | Required | Description |
|---|---|---|---|
| `element_id` | `str` | Yes | Unique element identifier from CFM or CSM |
| `element_name` | `str` | Yes | Human-readable element name |
| `element_type` | `str` | Yes | Element category (e.g., "functional_process", "decision", "business_rule") |
| `source_model` | `Literal["CFM", "CSM"]` | Yes | Which canonical model the element comes from |
| `raw_score` | `float` | Yes | `structural_score + content_score` |
| `normalized_value` | `int` | Yes | Fibonacci value from relative ranking (1, 2, 3, 5, 8, 13, 20, 40, 100) |
| `rank_position` | `int` | Yes | Position in ascending sort (0 = lowest raw score) |
| `structural_score` | `float` | Yes | Factor weighted sum (FPs) or base weight (all others) |
| `content_tokens` | `int` | Yes | Token count of `name + " " + description` |
| `content_score` | `float` | Yes | `content_tokens * content_multiplier` |
| `factor_breakdown` | `dict[str, float] \| None` | No | Per-factor weighted scores (FPs only; `None` for base-weight elements) |
| `base_weight` | `float \| None` | No | Base weight used (non-FP elements only; `None` for FPs) |
| `applied_rules` | `list[str]` | Yes | Rule identifiers applied (e.g., "factor_coefficients", "base_weight_default") |
| `evidence_refs` | `list[EvidenceRef]` | Yes | Traceability references to source specification |

**Constraints**:
- `raw_score == structural_score + content_score`
- `factor_breakdown` is non-None iff `element_type == "functional_process"`
- `base_weight` is non-None iff `element_type != "functional_process"`
- `sum(factor_breakdown.values()) == structural_score` (for FPs)

### StoryPointMeasurementResult (extended)

Aggregated measurement result for one specification.

| Field | Type | Required | Description |
|---|---|---|---|
| `run_id` | `str` | Yes | Unique run identifier |
| `method` | `str` | Yes | Always `"StoryPoints"` |
| `scale` | `str` | Yes | Always `"ModifiedFibonacci"` |
| `total_raw_score` | `float` | Yes | Sum of all `raw_score` values (cross-spec comparison) |
| `total_normalized_points` | `int` | Yes | Sum of all `normalized_value` values |
| `items` | `list[WorkItem]` | Yes | All estimated elements |
| `distribution` | `dict[int, int]` | Yes | Histogram: `{fibonacci_value: count}` |
| `specification_effort_total` | `float` | Yes | Sum of raw scores from CSM elements |
| `implementation_effort_total` | `float` | Yes | Sum of raw scores from CFM elements |
| `content_multiplier` | `float` | Yes | Multiplier used for this run |
| `content_tokens_by_type` | `dict[str, int]` | Yes | Total content tokens per element type |
| `calibration_version` | `str` | Yes | Version of the calibration profile used |
| `execution_metadata` | `ExecutionMetadata` | Yes | Performance and processing stats |
| `warnings` | `list[MeasurementWarning]` | Yes | Informational notices and warnings |
| `measured_at` | `datetime` | Yes | Measurement timestamp |

**Constraints**:
- `total_raw_score == sum(item.raw_score for item in items)`
- `specification_effort_total + implementation_effort_total == total_raw_score`
- `distribution` must match aggregated normalized values from items

### ExecutionMetadata (extended)

| Field | Type | Required | Description |
|---|---|---|---|
| `duration_ms` | `float` | Yes | Wall-clock execution time |
| `total_elements_processed` | `int` | Yes | All elements considered (CFM + CSM) |
| `cfm_elements_processed` | `int` | Yes | CFM elements processed |
| `csm_elements_processed` | `int` | Yes | CSM elements processed |
| `fps_estimated` | `int` | Yes | Unique functional processes estimated |
| `fps_merged_as_duplicates` | `int` | Yes | Duplicate FPs skipped |
| `elements_without_base_weight` | `int` | Yes | Elements using default fallback weight |
| `version` | `str` | Yes | Engine version |

**Constraints**:
- `total_elements_processed == cfm_elements_processed + csm_elements_processed`
- `total_elements_processed >= fps_estimated + fps_merged_as_duplicates`

### MeasurementWarning (unchanged)

| Field | Type | Required | Description |
|---|---|---|---|
| `code` | `str` | Yes | Warning code (e.g., "NO_FPS_FOUND", "UNKNOWN_ELEMENT_TYPE", "FALLBACK_WEIGHT_USED") |
| `message` | `str` | Yes | Human-readable description |
| `element_id` | `str \| None` | No | Related element, if applicable |

### EvidenceRef (unchanged)

| Field | Type | Required | Description |
|---|---|---|---|
| `graph_node_id` | `str` | Yes | Evidence graph node reference |
| `document_id` | `str` | Yes | Source document identifier |
| `section_id` | `str \| None` | No | Source section, if applicable |
| `text` | `str` | Yes | Relevant text fragment |

### StoryPointsCalibrationProfile

External calibration configuration (YAML file).

| Field | Type | Default | Description |
|---|---|---|---|
| `version` | `str` | `"1.0"` | Profile format version |
| `content_multiplier` | `float` | `0.1` | Content token multiplier |
| `factor_coefficients` | `dict[str, float]` | 6 defaults | Per-factor weights for FP scoring |
| `csm_base_weights` | `dict[str, float]` | 13 defaults | CSM element base weights |
| `cfm_base_weights` | `dict[str, float]` | 5 defaults | Non-FP CFM element base weights |
| `default_fallback_weight` | `float` | `1.0` | Weight for unknown element types |
| `fibonacci_scale` | `list[int]` | `[1,2,3,5,8,13,20,40,100]` | Output Fibonacci values |
| `ranking_strategy` | `str` | `"percentile"` | Band distribution strategy |

**Constraints**:
- `len(fibonacci_scale) >= 2` (need at least min and max)
- All weights must be `>= 0.0`
- `content_multiplier >= 0.0`

## State Transitions

Story Points measurement is stateless — there are no state transitions. Each `measure()` call produces an independent `StoryPointMeasurementResult`. The calibration profile is loaded once per run and remains immutable during computation.

## Entity Relationships

```
StoryPointsCalibrationProfile ──configures──► StoryPointsPlugin.measure()
                                                      │
                                                      │ produces
                                                      ▼
                                              StoryPointMeasurementResult
                                                      │
                                              ┌───────┴────────┐
                                              │                │
                                     WorkItem (CFM)    WorkItem (CSM)
                                     source=CFM         source=CSM
                                     factor_breakdown   base_weight
```

## Aggregation

The `aggregate()` function merges multiple `StoryPointMeasurementResult` objects:

1. Sum `total_raw_score`, `total_normalized_points`
2. Sum `specification_effort_total`, `implementation_effort_total`
3. Concatenate `items` lists
4. Sum `execution_metadata` counters
5. Merge `distribution` histograms (add counts)
6. Merge `content_tokens_by_type` (add counts)
7. Merge `warnings` (deduplicate by code+element_id)
8. Use format `"aggregated:{run_ids}"` for `run_id`
