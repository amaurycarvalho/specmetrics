# Data Model: T-Shirt Sizing Improvements

**Feature**: 041-tshirt-sizing  
**Date**: 2026-07-21

## Entity Overview

```
TShirtSize (mapping config) ──► TShirtClassifier ──► TShirtMeasurementResult
                                                          │
                                                          ├── total_items: int
                                                          ├── distribution: dict[str, int]
                                                          │
                                                          └── items: list[FunctionalWorkItem] (*)
                                                                   │
                                                                   ├── element_id: str
                                                                   ├── element_name: str
                                                                   ├── story_point_value: int
                                                                   ├── tshirt_size: str
                                                                   ├── mapping_rule: str
                                                                   └── evidence_refs: list
```

## Core Entities

### TShirtSize

Defines a single mapping entry in the classification table.

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | `str` | Yes | T-shirt size label: XS, S, M, L, XL, XXL |
| `story_point_range` | `tuple[int, int]` | Yes | Inclusive range of Story Point values mapping to this size |
| `ordinal` | `int` | Yes | Ordinal position (1=XS, 2=S, ..., 6=XXL) for sorting |

**Constraints**:
- `story_point_range[0] <= story_point_range[1]`
- `label` must be unique within a mapping
- Ranges must not overlap within a mapping
- Ranges must be sorted by `story_point_range[0]` ascending

**Default values** (updated):

| label | story_point_range | ordinal |
|---|---|---|
| XS | (1, 1) | 1 |
| S | (2, 3) | 2 |
| M | (5, 5) | 3 |
| L | (8, 13) | 4 |
| XL | (20, 40) | 5 |
| XXL | (100, 100) | 6 |

### FunctionalWorkItem (unchanged structure)

Represents a single entity after T-shirt classification.

| Field | Type | Required | Description |
|---|---|---|---|
| `element_id` | `str` | Yes | Entity identifier from the source specification |
| `element_name` | `str` | Yes | Human-readable entity name |
| `story_point_value` | `int` | Yes | The normalized Fibonacci value that produced this classification |
| `tshirt_size` | `str` | Yes | Assigned T-shirt size label (XS, S, M, L, XL, XXL) or "UNKNOWN" |
| `mapping_rule` | `str` | Yes | Human-readable rule (e.g., `"default: 8-13 → L"`) |
| `evidence_refs` | `list[MeasurementEvidence]` | Yes | Traceability references |
| `applied_rule_pack` | `str` | Yes | Rule pack identifier (default: `"default"`) |

### MeasurementEvidence (unchanged)

| Field | Type | Required | Description |
|---|---|---|---|
| `element_id` | `str` | Yes | Entity identifier |
| `story_point_value` | `int` | Yes | Story Point value used for classification |
| `mapping_rule` | `str` | Yes | Rule that produced the classification |
| `document_id` | `str` | No | Source document |
| `section_id` | `str \| None` | No | Source section |

### MeasurementWarning (unchanged)

| Field | Type | Required | Description |
|---|---|---|---|
| `code` | `str` | Yes | Warning code: `"NO_STORY_POINTS"`, `"MISSING_SP_VALUE"`, or `"UNKNOWN_SIZE"` |
| `message` | `str` | Yes | Human-readable description |
| `element_id` | `str \| None` | No | Related entity, if applicable |

### ExecutionMetadata (unchanged)

| Field | Type | Required | Description |
|---|---|---|---|
| `duration_ms` | `float` | Yes | Wall-clock execution time |
| `total_fps_processed` | `int` | Yes | Number of Story Point items processed |
| `version` | `str` | Yes | Engine version (`"1.0"`) |

### TShirtMeasurementResult (unchanged structure; expanded payload)

| Field | Type | Required | Description |
|---|---|---|---|
| `run_id` | `str` | Yes | Unique run identifier |
| `method` | `str` | Yes | Always `"TShirtSizing"` |
| `scale` | `str` | Yes | Always `"XS-S-M-L-XL-XXL"` |
| `total_items` | `int` | Yes | Number of entities classified |
| `items` | `list[FunctionalWorkItem]` | Yes | All classified entities |
| `distribution` | `dict[str, int]` | Yes | Count per size: `{"XS": 3, "S": 8, ...}` |
| `applied_rule_pack` | `str` | Yes | Rule pack identifier |
| `execution_metadata` | `ExecutionMetadata` | Yes | Performance stats |
| `source_measurement_run_id` | `str` | Yes | Source Story Points run ID |
| `warnings` | `list[MeasurementWarning]` | Yes | Notices and warnings |
| `measured_at` | `datetime` | Yes | Measurement timestamp |

**Constraints**:
- `total_items == len(items)`
- `distribution` must match aggregated item counts

### Pipeline Payload Extensions (new/modified keys)

The T-Shirt handler writes these keys to `ctx.measurement_result` via `merge_stage_output`:

| Key | Type | Description |
|---|---|---|
| `tshirt` *(new)* | `int` | Total entity count — used by orchestrator for measure.json total |
| `tshirt_breakdown` *(new)* | `dict[str, dict]` | Per-size breakdown: `{"XS": {"count": 3}, ...}` — used for measure.json breakdown |
| `tshirt_entities` | `list[dict]` | Serialized `FunctionalWorkItem` list — used by metrics.json entity builder |
| `method` | `str` | `"TShirtSizing"` |
| `scale` | `str` | `"XS-S-M-L-XL-XXL"` |
| `total_items` | `int` | Entity count (legacy, retained for compatibility) |
| `distribution` | `dict[str, int]` | Size distribution (retained for compatibility) |
| `source_measurement_run_id` | `str` | Source Story Points run |
| `duration_ms` | `float` | Execution time |
| `warnings` | `list[dict]` | Serialized warnings |

## Output Format Contracts

### measure.json Entry (via orchestrator stage entities)

```json
{
  "metric": "tshirt",
  "total": 42,
  "status": "completed",
  "duration_ms": 15,
  "breakdown": {
    "XS": { "count": 3 },
    "S": { "count": 8 },
    "M": { "count": 12 },
    "L": { "count": 10 },
    "XL": { "count": 7 },
    "XXL": { "count": 2 }
  }
}
```

### metrics.json Entry (via MetricBreakdownEntry)

```json
{
  "name": "tshirt",
  "metric": "tshirt",
  "total": 42,
  "unit": "entities",
  "entity_count": 42,
  "entities": [
    {
      "id": "cfm:functional_process:process-order",
      "name": "Process Order",
      "type": "functional_process",
      "story_point_value": 8,
      "tshirt_size": "L",
      "mapping_rule": "default: 8-13 → L"
    }
  ],
  "status": "success",
  "metadata": {
    "scale": "XS-S-M-L-XL-XXL",
    "mapping": {
      "XS": 1,
      "S": 3,
      "M": 5,
      "L": 8,
      "XL": 13,
      "XXL": 100
    }
  }
}
```

### CLI Display

```
Results:
  ...
  FPA: 123.0
  Story Points: 42
  TShirt: 42 entities
    XS: 3  S: 8  M: 12  L: 10  XL: 7  XXL: 2
```

## State Transitions

T-Shirt Sizing is stateless — each classification run is independent. The mapping table is loaded once at handler initialization and remains immutable during execution.
