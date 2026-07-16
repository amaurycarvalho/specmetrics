# Data Model: SFP Measurement Engine

## Overview

Data entities for the SFP (Simple Function Points) measurement plugin. These models represent the measurement output — the result of applying deterministic counting rules to the Canonical Functional Model (F06). They are consumed by Export Layer (F10) and Publisher (F11) plugins.

## Entity Definitions

### SFPMeasurementResult

Top-level container for a complete SFP measurement.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `str` | Unique pipeline run identifier, sourced from pipeline context |
| `cfm_run_id` | `str` | Source Canonical Functional Model run_id |
| `rule_pack_id` | `Optional[str]` | Identifier of the applied Rule Pack (null if default rules used) |
| `measured_components` | `list[MeasuredComponent]` | All measured components with evidence |
| `summary` | `MeasurementSummary` | Aggregated counts and totals |
| `explanations` | `list[MeasurementExplanation]` | Per-component explanations with evidence trails |
| `warnings` | `list[MeasurementWarning]` | Non-fatal issues encountered during measurement |
| `errors` | `list[MeasurementError]` | Fatal errors that prevented complete measurement |
| `measured_at` | `datetime` | Timestamp of measurement completion |

**Validation Rules**:
- If `errors` is non-empty, `summary.total_sfp` must be null (no partial results on error)
- All `measured_component[i].id` values must be unique
- `summary.total_component_count` must equal `len(measured_components)`

**State Transitions**:
- `Pending` (initial) → `Complete` (after measurement finishes) — no partial states; if interrupted, result is discarded

---

### MeasuredComponent

A single measured SFP component (Functional Process or Logical Function).

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the measurement result |
| `name` | `str` | Component name, derived from originating CFM element |
| `component_type` | `ComponentType` | SFP classification: `functional_process` or `logical_function` |
| `contribution` | `float` | Fixed SFP contribution value for this component type |
| `cfm_element_id` | `str` | ID of the originating CFM element |
| `cfm_element_type` | `str` | CFM entity type that originated this component (e.g., `ElementaryProcess`, `DataGroup`) |
| `evidence_refs` | `list[EvidenceRef]` | Evidence trail back to specification fragments |
| `rule_applied` | `Optional[str]` | Identifier of the specific counting rule applied (for Rule Pack overrides) |

**Validation Rules**:
- `component_type` must be one of the two recognized SFP types
- `contribution` must be a positive number matching the fixed value for the component type (unless overridden by Rule Pack)

---

### MeasurementSummary

Aggregated totals and breakdowns.

| Field | Type | Description |
|-------|------|-------------|
| `total_component_count` | `int` | Total number of measured components |
| `total_sfp` | `float` | Total Simple Function Points |
| `by_type` | `dict[ComponentType, TypeBreakdown]` | Breakdown of counts and SFP per component type |

---

### TypeBreakdown

Count and SFP subtotal for a single component type.

| Field | Type | Description |
|-------|------|-------------|
| `count` | `int` | Number of components of this type |
| `total_sfp` | `float` | Sum of SFP contributions for this type |

---

### MeasurementExplanation

A human-readable explanation of how a specific component was measured.

| Field | Type | Description |
|-------|------|-------------|
| `component_id` | `str` | Reference to the MeasuredComponent |
| `cfm_element_id` | `str` | Originating CFM element |
| `cfm_element_name` | `str` | Name of the originating CFM element |
| `identification_reason` | `str` | Why this element was classified as the component type (e.g., "CFM node_type='elementary_process' → Functional Process") |
| `contribution_reason` | `str` | How the contribution value was determined (e.g., "Default SFP weight for Functional Processes") |
| `rule_exceptions` | `list[str]` | Any Rule Pack overrides applied to this component |
| `evidence_chain` | `list[str]` | Ordered list of trace steps: specification section → evidence graph node → CFM element → measured component |

---

### MeasurementWarning

Non-fatal issue encountered during measurement.

| Field | Type | Description |
|-------|------|-------------|
| `code` | `str` | Machine-readable warning code |
| `message` | `str` | Human-readable description |
| `cfm_element_id` | `Optional[str]` | Related CFM element (if applicable) |
| `details` | `Optional[dict[str, str]]` | Additional context |

---

### MeasurementError

Fatal error that prevents complete measurement.

| Field | Type | Description |
|-------|------|-------------|
| `code` | `str` | Machine-readable error code |
| `message` | `str` | Human-readable description |
| `cfm_element_id` | `Optional[str]` | Related CFM element (if applicable) |
| `recoverable` | `bool` | Whether measurement can continue with partial results |

---

### EvidenceRef

Reference to originating evidence, mirroring the CFM EvidenceRef structure.

| Field | Type | Description |
|-------|------|-------------|
| `graph_node_id` | `str` | ID of the source node in the evidence graph |
| `document_id` | `str` | Originating document identifier |
| `section_id` | `Optional[str]` | Section within the document (if applicable) |
| `text` | `str` | Source text fragment |

---

## Enumerations

### ComponentType

```python
Literal["functional_process", "logical_function"]
```

## Classification Mapping

CFM entities are classified to SFP component types using these deterministic rules:

| CFM Element Type | CFM Attribute Condition | SFP Component Type |
|-----------------|------------------------|-------------------|
| `elementary_process` | `node_type == "elementary_process"` | `functional_process` |
| `data_group` | `node_type == "data_group"` and represents user-recognizable business information | `logical_function` |

**Duplicate Merging**:
- Duplicates are identified by CFM node ID AND content fingerprint (SHA-256 of `document_id`, `section_id`, `text`, `semantic_type`)
- Matching duplicates are merged into a single MeasuredComponent (only one contributes to total SFP)
- A warning is emitted for each merged duplicate

## Immutability

Once constructed, `SFPMeasurementResult` is immutable. This guarantees:
- Deterministic export: identical result → identical export output
- Audit trail: measurement as-produced is preserved for verification
- Thread safety: concurrent consumers (export, publish) read without synchronization
