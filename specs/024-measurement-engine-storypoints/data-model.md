# Data Model: Story Points Measurement

## Overview

All measurement models are Pydantic `BaseModel` instances. `StoryPointMeasurementResult` is the top-level result. Results are immutable once created.

## StoryPointMeasurementResult

```python
class StoryPointMeasurementResult(BaseModel):
    run_id: str                                          # Pipeline run ID
    method: str = "StoryPoints"
    scale: str = "ModifiedFibonacci"
    total_story_points: int                              # Sum of all normalized values
    items: list[FunctionalWorkItem]                      # Per-work-item estimates
    distribution: dict[int, int] = {}                    # value → count
    applied_rule_pack: str = "default"
    execution_metadata: ExecutionMetadata
    warnings: list[MeasurementWarning] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Validation rules**:
- `total_story_points` MUST equal sum of all `item.normalized_value`
- `distribution` MUST match aggregated item values
- All `normalized_value` entries MUST be in the configured Fibonacci scale
- `run_id` MUST be non-empty

---

## FunctionalWorkItem

```python
class FunctionalWorkItem(BaseModel):
    element_id: str                                      # UUID of the Functional Process
    element_name: str                                    # Human-readable name
    raw_score: float                                     # Pre-normalization score
    normalized_value: int                                # Final Fibonacci value
    factor_breakdown: dict[str, float]                   # Per-factor scores with coefficients applied
    applied_rules: list[str] = []                        # Rule identifiers applied
    evidence_refs: list[EvidenceRef] = []                 # Provenance links to CFM
```

---

## RawEffortScore

```python
class RawEffortScore(BaseModel):
    value: float                                         # Total raw effort score
    factor_breakdown: dict[str, float]                   # per-factor: score × coefficient
    factor_coefficients: dict[str, float]                # The coefficients that were applied
```

---

## StoryPointEstimate

```python
class StoryPointEstimate(BaseModel):
    value: int                                           # From the configured Fibonacci scale
    raw_score: float                                     # Input raw score
    normalization_rule: str                              # e.g., "default_threshold_v1"
```

---

## MeasurementEvidence

```python
class MeasurementEvidence(BaseModel):
    element_id: str                                      # CFM node ID
    document_id: str                                     # Originating document
    section_id: str | None = None                        # Originating section
    applied_rule: str = ""                               # Rule applied at this step
    text: str = ""                                       # Supporting text excerpt
```

---

## ExecutionMetadata

```python
class ExecutionMetadata(BaseModel):
    duration_ms: float = 0.0
    total_fps_processed: int = 0
    fps_estimated: int = 0
    fps_merged_as_duplicates: int = 0
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

## EvidenceRef

```python
class EvidenceRef(BaseModel):
    graph_node_id: str
    document_id: str
    section_id: str | None = None
    text: str
```

---

## Entity Relationships

```
PipelineContext
    └── canonical_model (CFM) ──────────────────────┐
                                                      ▼
                                        StoryPointMeasurementResult
                                        ├── items: list[FunctionalWorkItem]
                                        │     ├── raw_score (multi-factor weighted sum)
                                        │     ├── normalized_value (Fibonacci)
                                        │     ├── factor_breakdown
                                        │     └── evidence_refs
                                        ├── distribution
                                        ├── total_story_points
                                        └── execution_metadata
```

The calculator iterates Functional Processes from the CFM. For each process:
1. Compute per-factor scores using `factor_scorer` (reads related actors, data groups, operations, business rules, relationships from the CFM)
2. Apply coefficients (from built-in defaults or Rule Pack overrides)
3. Sum for raw effort score
4. Normalize via `normalizer` to nearest Fibonacci value
5. Package as `FunctionalWorkItem`

---

## Validation Rules

| Field | Rule |
|-------|------|
| `StoryPointMeasurementResult.total_story_points` | Must equal sum of `item.normalized_value` |
| `FunctionalWorkItem.normalized_value` | Must be in the configured Fibonacci scale |
| `FunctionalWorkItem.raw_score` | Must equal sum of `factor_breakdown` values |
| `ExecutionMetadata.total_fps_processed` | Must equal `fps_estimated + fps_merged_as_duplicates` |
| `ExecutionMetadata.duration_ms` | Must be non-negative |

## State Transitions

Measurement results are immutable once created. Factor coefficients and normalization thresholds are configurable via Rule Packs applied before measurement execution (per FR-030 pipeline order). Incremental execution tracks fingerprint changes between runs but does not mutate previous results.
