# Data Model: Token Points Measurement

## Overview

All measurement models are Pydantic `BaseModel` instances. The `TokenPointsMeasurement` is the top-level result. Results are immutable (standard Pydantic, no `frozen=True` required since they are reported, not stored).

## TokenPointsMeasurement

```python
class TokenPointsMeasurement(BaseModel):
    run_id: str                                          # Pipeline run ID
    total_score: float                                   # Specification Cost + Code Generation Cost
    specification_cost: SpecificationCost                # CSM-derived cost component
    code_generation_cost: CodeGenerationCost             # CFM-derived cost component
    calibration_version: str = "1.0"                     # Applied calibration version
    measurement_metadata: MeasurementMetadata            # Timing, counts, warnings
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Validation rules**:
- `total_score` MUST equal `specification_cost.total + code_generation_cost.total`
- `run_id` MUST be non-empty

---

## SpecificationCost

```python
class SpecificationCost(BaseModel):
    total: float                                    # Sum of all specification contributions
    contributions: list[TokenContribution]           # Per-element breakdown
```

---

## CodeGenerationCost

```python
class CodeGenerationCost(BaseModel):
    total: float                                    # Sum of all code generation contributions
    contributions: list[TokenContribution]           # Per-element breakdown
```

---

## TokenContribution

```python
class TokenContribution(BaseModel):
    element_id: str                                 # UUID of the canonical element
    element_type: str                               # e.g., "decision", "functional_process"
    element_name: str                               # Human-readable name
    model_source: Literal["cfm", "csm"]             # Originating model
    applied_weight: float                           # Weight from calibration profile
    partial_score: float                            # weight × 1.0 (always equals weight in v0.1)
    evidence_ref: EvidenceRef | None = None         # Provenance link to evidence graph
```

---

## MeasurementMetadata

```python
class MeasurementMetadata(BaseModel):
    total_elements_processed: int = 0               # Combined CFM + CSM element count
    csm_element_count: int = 0                      # CSM elements processed
    cfm_element_count: int = 0                      # CFM elements processed
    duration_ms: float = 0.0                        # Measurement execution time
    warnings: list[MeasurementWarning] = []         # Non-fatal issues (e.g., missing CSM)
    calibration_profile_applied: str = "built-in"   # Profile name or "built-in"
```

---

## MeasurementWarning

```python
class MeasurementWarning(BaseModel):
    code: str
    message: str
    details: dict[str, str] | None = None
```

---

## CalibrationProfile

```python
class SpecificationCostWeights(BaseModel):
    activities: dict[str, float]                     # activity_type → weight
    decisions: float = 1.5
    assumptions: float = 1.0
    constraints: float = 1.5
    risks: float = 2.0
    open_questions: float = 1.0
    acceptance_criteria: float = 1.0
    glossary_terms: float = 0.5

class CodeGenerationCostWeights(BaseModel):
    functional_processes: float = 5.0
    business_rules: float = 3.0
    operations: float = 2.0
    data_groups: float = 2.0
    relationships: float = 1.0
    actors: float = 1.0

class CalibrationProfile(BaseModel):
    version: str = "1.0"
    specification_cost: SpecificationCostWeights = Field(default_factory=SpecificationCostWeights)
    code_generation_cost: CodeGenerationCostWeights = Field(default_factory=CodeGenerationCostWeights)
```

---

## Entity Relationships

```
PipelineContext
    ├── canonical_model (CFM) ──────────────────┐
    │                                             │
    ├── canonical_spec_model (CSM) ──────────────┤
    │                                             ▼
    │                              TokenPointsMeasurement
    │                              ├── specification_cost
    │                              │     ├── total: float
    │                              │     └── contributions: list[TokenContribution]
    │                              │           └── model_source: "csm"
    │                              ├── code_generation_cost
    │                              │     ├── total: float
    │                              │     └── contributions: list[TokenContribution]
    │                              │           └── model_source: "cfm"
    │                              └── measurement_metadata
    │
    └── calibration_metadata ──── CalibrationProfile
                                       ├── specification_cost (weights per CSM entity)
                                       └── code_generation_cost (weights per CFM entity)
```

The Token Points handler reads both canonical models from PipelineContext, loads the CalibrationProfile (from built-in defaults or YAML), iterates over each element collection, applies the corresponding weight, and accumulates contributions into the two cost components.

---

## Validation Rules

| Field | Rule |
|-------|------|
| `TokenPointsMeasurement.total_score` | Must equal `specification_cost.total + code_generation_cost.total` |
| `TokenContribution.partial_score` | Must equal `applied_weight` (simple sum in v0.1) |
| `MeasurementMetadata.csm_element_count` | Must equal len of all CSM contributions combined |
| `MeasurementMetadata.cfm_element_count` | Must equal len of all CFM contributions combined |
| `CalibrationProfile.version` | Must be a valid semver string |

## State Transitions

Measurement results are immutable once created (standard Pydantic immutability is sufficient; no frozen model required since results are reported, not modified). CalibrationProfile is loaded once at measurement time and not mutated.
