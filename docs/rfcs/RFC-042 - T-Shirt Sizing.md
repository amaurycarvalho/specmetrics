# RFC-042: T-Shirt Sizing

**Status**: Draft  
**Date**: 2026-07-21  
**Author**: SpecMetrics

## Methodology Overview

[T-Shirt Sizing](https://asana.com/pt/resources/t-shirt-sizing) is a classification layer that maps normalized Story Point values (Modified Fibonacci: 1, 2, 3, 5, 8, 13, 20, 40, 100) into six ordinal effort categories: XS, S, M, L, XL, XXL.

The classification is a deterministic lookup-table mapping. Each size corresponds to a range of Story Point values. The mapping is configurable, allowing teams to adjust thresholds based on their historical velocity.

### Relationship to Story Points

T-Shirt Sizing takes the output of the Story Points measurement engine and groups entities into coarse effort buckets. It does not replace Story Points — it provides a higher-level abstraction useful for:

- Dashboard and report summarization
- Cross-specification comparison at category level
- Quick communication of effort distribution to stakeholders
- Kanban work-item sizing guidance

## Mapping Table

### Default Mapping

The 9 Modified Fibonacci values are distributed across 6 sizes:

| Size | Story Point Range | Ordinal | Rationale                             |
| ---- | ----------------- | ------- | ------------------------------------- |
| XS   | 1                 | 1       | Trivial — single value, atomic effort |
| S    | 2–3               | 2       | Small — two adjacent low values       |
| M    | 5                 | 3       | Medium — single midpoint value        |
| L    | 8–13              | 4       | Large — two moderate values           |
| XL   | 20–40             | 5       | Extra large — two high values         |
| XXL  | 100               | 6       | Extreme — maximum single value        |

Every Fibonacci value maps to exactly one size. All 6 sizes are covered. No value produces UNKNOWN under the default mapping.

### Configuration

The mapping is defined as a list of `TShirtSize` entries, each with:

- `label`: The size name (e.g., "XS", "S", ..., "XXL")
- `story_point_range`: Inclusive `[min, max]` tuple of Story Point values
- `ordinal`: Sorting order (1 = smallest, 6 = largest)

Custom mappings can be provided via pipeline metadata (`tshirt_mapping` key). Validation rules:

- Ranges must not overlap
- Labels must be unique
- At least one size is required
- Ranges must have `min <= max`

## Output Formats

### measure.json Entry

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

- `total`: Number of entities classified (entity count, not a sum of values)
- `breakdown`: Per-size counts. Sum of counts equals `total`.

### metrics.json Entry

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
      "score": 8.0,
      "metadata": {
        "story_point_value": 8,
        "tshirt_size": "L",
        "mapping_rule": "default: 8-13 → L"
      }
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
  Story Points: 42
  TShirt: 42 entities
    XS: 3  S: 8  M: 12  L: 10  XL: 7  XXL: 2
```

## Usage Guidance

### Cross-Specification Comparison

T-Shirt distributions enable coarse-grained comparison across specifications. Two specifications with different Story Point distributions will produce measurably different T-Shirt size proportions. For example, a specification dominated by large functional processes will have a higher proportion of L/XL/XXL items compared to one with small, simple processes.

### Kanban Work Item Sizing

T-Shirt sizes provide a quick heuristic for manual work item sizing in Kanban:

- **XS/S**: Small changes, quick wins
- **M**: Typical work item, fits in a single iteration
- **L/XL**: Large items that may need decomposition
- **XXL**: Very large items that should be decomposed

Specification decomposition into equal-effort work items is a manual practice. SpecMetrics provides the classification data that enables this practice but does not implement automatic chunking or splitting functionality.
