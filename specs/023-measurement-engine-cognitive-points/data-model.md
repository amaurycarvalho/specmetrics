# Data Model: Cognitive Points Measurement

## Overview

All measurement models are Pydantic `BaseModel` instances. `CognitivePointsMeasurement` is the top-level result. Results are immutable once created.

## CognitivePointsMeasurement

```python
class CognitivePointsMeasurement(BaseModel):
    run_id: str                                              # Pipeline run ID
    total_cognitive_points: int                              # Normalized Fibonacci value
    raw_score: float                                         # Pre-normalization total
    specification_review_effort: SpecificationReviewEffort   # CSM-derived component
    functional_validation_effort: FunctionalValidationEffort # CFM-derived component
    fibonacci_normalization: FibonacciNormalizationResult    # Threshold applied
    calibration_version: str = "1.0"
    measurement_metadata: MeasurementMetadata
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Validation rules**:
- `raw_score` MUST equal `specification_review_effort.total_raw + functional_validation_effort.total_raw`
- `total_cognitive_points` MUST equal the Fibonacci output value for `raw_score`
- `run_id` MUST be non-empty

---

## SpecificationReviewEffort

```python
class SpecificationReviewEffort(BaseModel):
    total_raw: float                                    # Sum of Bloom-weighted CSM contributions
    contributions: list[CognitiveContribution]            # Per-element breakdown
    bloom_breakdown: dict[str, int]                      # e.g., {"analyze": 5, "evaluate": 3}
```

---

## FunctionalValidationEffort

```python
class FunctionalValidationEffort(BaseModel):
    total_raw: float                                    # Sum of Bloom-weighted CFM contributions
    contributions: list[CognitiveContribution]            # Per-element breakdown
    bloom_breakdown: dict[str, int]                      # e.g., {"create": 2, "apply": 4}
```

---

## CognitiveContribution

```python
class CognitiveContribution(BaseModel):
    element_id: str                                 # UUID of the canonical element
    element_type: str                               # e.g., "decision", "functional_process"
    element_name: str                               # Human-readable name
    model_source: Literal["cfm", "csm"]             # Originating model
    bloom_level: str                                # e.g., "analyze", "evaluate"
    cognitive_weight: float                         # Weight for the assigned Bloom level
    partial_score: float                            # cognitive_weight × 1.0
    evidence_ref: EvidenceRef | None = None         # Provenance link
```

---

## FibonacciNormalizationResult

```python
class FibonacciNormalizationResult(BaseModel):
    raw_score: float                                 # Input to normalization
    threshold_applied: float                         # Lower bound of matching threshold
    output_value: int                                # Normalized Fibonacci value
```

---

## MeasurementMetadata

```python
class MeasurementMetadata(BaseModel):
    total_elements_processed: int = 0
    csm_element_count: int = 0
    cfm_element_count: int = 0
    bloom_distribution: dict[str, int] = {}          # Count of elements per Bloom level
    duration_ms: float = 0.0
    warnings: list[MeasurementWarning] = []
    calibration_profile_applied: str = "built-in"
```

---

## BloomClassification

```python
class BloomClassification(BaseModel):
    bloom_level: str                                 # One of: remember, understand, apply, analyze, evaluate, create
    rationale: str = ""                              # Why this level was assigned
    configured_weight: float = 1.0
```

---

## FibonacciNormalizationProfile

```python
class FibonacciNormalizationProfile(BaseModel):
    thresholds: list[float]                          # Ascending thresholds between values
    output_values: list[int]                         # Corresponding Fibonacci values

    @model_validator(mode="after")
    def validate_lengths(cls, values):
        assert len(values.output_values) == len(values.thresholds) + 1
        return values
```

---

## CognitiveCalibrationProfile

```python
class CognitiveCalibrationProfile(BaseModel):
    version: str = "1.0"
    bloom_levels: dict[str, float]                   # bloom_level → weight (e.g., "analyze": 4.0)
    bloom_mappings: dict[str, str]                   # element_type → bloom_level
    default_bloom_level: str = "analyze"
    fibonacci_normalization: FibonacciNormalizationProfile
```

---

## Entity Relationships

```
PipelineContext
    ├── canonical_model (CFM) ──────────────────┐
    ├── canonical_spec_model (CSM) ─────────────┤
    │                                            ▼
    │                             CognitivePointsMeasurement
    │                             ├── specification_review_effort
    │                             │     ├── total_raw: float
    │                             │     ├── contributions: list[CognitiveContribution]
    │                             │     └── bloom_breakdown: dict[str, int]
    │                             ├── functional_validation_effort
    │                             │     ├── total_raw: float
    │                             │     ├── contributions: list[CognitiveContribution]
    │                             │     └── bloom_breakdown: dict[str, int]
    │                             ├── fibonacci_normalization
    │                             │     ├── raw_score
    │                             │     ├── threshold_applied
    │                             │     └── output_value
    │                             └── measurement_metadata
    │
    └── calibration ─────────── CognitiveCalibrationProfile
                                    ├── bloom_levels (level → weight)
                                    ├── bloom_mappings (element_type → level)
                                    └── fibonacci_normalization (thresholds + values)
```

---

## Validation Rules

| Field | Rule |
|-------|------|
| `CognitivePointsMeasurement.raw_score` | Must equal sum of both component `total_raw` values |
| `CognitivePointsMeasurement.total_cognitive_points` | Must match Fibonacci output for `raw_score` |
| `CognitiveContribution.partial_score` | Must equal `cognitive_weight` (simple sum in v0.1) |
| `MeasurementMetadata.csm_element_count` | Must equal count of `model_source == "csm"` contributions |
| `MeasurementMetadata.cfm_element_count` | Must equal count of `model_source == "cfm"` contributions |
| `MeasurementMetadata.bloom_distribution` | Must equal merged `bloom_breakdown` from both components |
| `FibonacciNormalizationProfile` | `len(output_values)` == `len(thresholds) + 1` |

## State Transitions

Measurement results are immutable once created. CalibrationProfile is loaded once at measurement time and not mutated. Fibonacci normalization is a pure function of raw_score.
