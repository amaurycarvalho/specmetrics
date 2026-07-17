# Data Model: T-Shirt Sizing Measurement

## Overview

All measurement models are Pydantic `BaseModel` instances. `TShirtMeasurementResult` is the top-level result. This is the simplest data model in the measurement plugin suite — essentially a classified view over Story Points.

## TShirtMeasurementResult

```python
class TShirtMeasurementResult(BaseModel):
    run_id: str                                          # Pipeline run ID
    method: str = "TShirtSizing"
    scale: str = "XS-S-M-L-XL-XXL"                       # Comma-joined size labels
    total_items: int = 0
    items: list[FunctionalWorkItem] = []                  # Per-item classifications
    distribution: dict[str, int] = {}                     # size_label → count
    applied_rule_pack: str = "default"
    execution_metadata: ExecutionMetadata
    source_measurement_run_id: str = ""                   # Run ID of the SP measurement
    warnings: list[MeasurementWarning] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Validation rules**:
- `total_items` MUST equal `len(items)`
- `distribution` MUST aggregate to match `total_items`
- Every `tshirt_size` value MUST be a key in `distribution`
- `run_id` MUST be non-empty

---

## FunctionalWorkItem

```python
class FunctionalWorkItem(BaseModel):
    element_id: str                                      # UUID of the originating Functional Process
    element_name: str                                    # Human-readable name
    story_point_value: int                               # The SP estimate consumed
    tshirt_size: str                                     # Assigned size (e.g., "M", "XL")
    mapping_rule: str = ""                                # Rule identifier or description
    evidence_refs: list[MeasurementEvidence] = []
    applied_rule_pack: str = "default"
```

---

## TShirtSize

```python
class TShirtSize(BaseModel):
    label: str                                           # e.g., "XS", "M", "XXL"
    story_point_range: tuple[int, int]                   # Inclusive [min, max]
    ordinal: int                                         # Sort position (1-based)
```

---

## MeasurementEvidence

```python
class MeasurementEvidence(BaseModel):
    element_id: str                                      # CFM node ID
    story_point_value: int                               # Originating SP estimate
    mapping_rule: str = ""
    document_id: str = ""
    section_id: str | None = None
```

---

## ExecutionMetadata

```python
class ExecutionMetadata(BaseModel):
    duration_ms: float = 0.0
    total_fps_processed: int = 0
    version: str = "1.0"
```

---

## MeasurementWarning

```python
class MeasurementWarning(BaseModel):
    code: str
    message: str
    element_id: str | None = None
```

---

## Entity Relationships

```
PipelineContext
    └── measurement_result (set by Story Points) ──────┐
                                                         ▼
                                             TShirtMeasurementResult
                                             ├── items: list[FunctionalWorkItem]
                                             │     ├── story_point_value (from SP result)
                                             │     ├── tshirt_size (from classifier lookup)
                                             │     └── evidence_refs
                                             ├── distribution
                                             ├── total_items
                                             └── execution_metadata
```

The classifier reads each `FunctionalWorkItem` from the Story Points result, looks up its `story_point_value` in the mapping table, assigns the corresponding `tshirt_size`, and packages as a new `FunctionalWorkItem` in the T-Shirt result.

---

## Validation Rules

| Field | Rule |
|-------|------|
| `TShirtMeasurementResult.total_items` | Must equal `len(items)` |
| `TShirtMeasurementResult.distribution` | Must equal `Counter(item.tshirt_size for item in items)` |
| `FunctionalWorkItem.tshirt_size` | Must be a valid label from the configured mapping table |
| `TShirtSize.story_point_range` | `min ≤ max`, ranges must not overlap |

## State Transitions

Results are immutable once created. Mapping table is loaded once at classification time and not mutated. Classification is stateless — same SP input + same mapping → same TShirt output.
