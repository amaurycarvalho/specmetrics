# Data Model: Business Complexity Points (BCP) Measurement

## Overview

All models are Pydantic `BaseModel` instances. `BCPMeasurementResult` is the top-level result. The SDK's return format `{"total_bcp": float, "breakdown": dict}` is preserved in `SDKResult`.

## BCPMeasurementResult

```python
class BCPMeasurementResult(BaseModel):
    run_id: str                                          # Pipeline run ID
    method: str = "BCP"
    sdk_version: str = ""                                # Version from bcp-calculator
    provider: str = "openai"                             # SDK provider used
    items: list[BCPWorkItem] = []                        # Per-work-item results
    total_bcp: float = 0.0                               # Sum of all item scores
    generated_stories: list[GeneratedStory] = []          # Stories submitted to SDK
    applied_rule_pack: str = "default"
    execution_metadata: ExecutionMetadata
    warnings: list[MeasurementWarning] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Validation rules**:
- `total_bcp` MUST equal sum of `item.bcp_score`
- `run_id` MUST be non-empty

---

## BCPWorkItem

```python
class BCPWorkItem(BaseModel):
    element_id: str                                      # UUID of originating Functional Process
    element_name: str                                    # Human-readable name
    generated_story: str                                 # Markdown story submitted to SDK
    sdk_response: dict[str, Any] = {}                    # Raw SDK response
    bcp_score: float                                     # Business Complexity Point score
    component_breakdown: dict[str, float] = {}            # Per-component breakdown from SDK
    evidence_refs: list[MeasurementEvidence] = []
    status: Literal["success", "failed", "skipped"] = "success"
```

---

## GeneratedStory

```python
class GeneratedStory(BaseModel):
    content: str                                         # Markdown user story string
    evidence_ref: MeasurementEvidence                     # Link to originating CFM node
```

---

## SDKResult

```python
class SDKResult(BaseModel):
    total_bcp: float                                     # From SDK response
    breakdown: dict[str, float] = {}                      # Per-component breakdown
    raw_response: dict[str, Any] = {}                     # Complete SDK response
    provider: str = "openai"
    duration_ms: float = 0.0
    warnings: list[str] = []
    errors: list[str] = []
```

---

## MeasurementEvidence

```python
class MeasurementEvidence(BaseModel):
    element_id: str
    document_id: str = ""
    section_id: str | None = None
    story_point_value: float | None = None
    text: str = ""
```

---

## ExecutionMetadata

```python
class ExecutionMetadata(BaseModel):
    duration_ms: float = 0.0
    total_fps_processed: int = 0
    items_succeeded: int = 0
    items_failed: int = 0
    sdk_call_count: int = 0
    sdk_errors: int = 0
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
    └── canonical_model (CFM) ──────────────────────┐
                                                      ▼
                                            BCPMeasurementResult
                                            ├── items: list[BCPWorkItem]
                                            │     ├── generated_story: str (markdown)
                                            │     ├── sdk_response: dict (raw SDK output)
                                            │     ├── bcp_score: float
                                            │     ├── component_breakdown
                                            │     └── evidence_refs
                                            ├── generated_stories
                                            ├── total_bcp
                                            └── execution_metadata
```

The plugin iterates Functional Processes from CFM. For each process: generate markdown story → call SDK via adapter → collect `total_bcp` + `breakdown` → package as `BCPWorkItem`.

---

## Validation Rules

| Field | Rule |
|-------|------|
| `BCPMeasurementResult.total_bcp` | Must equal sum of `item.bcp_score` for items with `status == "success"` |
| `ExecutionMetadata.total_fps_processed` | Must equal `items_succeeded + items_failed` |
| `BCPWorkItem.status` | Must be one of "success", "failed", "skipped" |

## State Transitions

Measurement results are immutable once created. SDK calls are stateless — same CFM story → SDK may return different results (non-deterministic by design, Principle IV not applicable).
