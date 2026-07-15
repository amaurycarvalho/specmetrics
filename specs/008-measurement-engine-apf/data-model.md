# Data Model: APF Measurement Engine

## Overview

Data entities for the APF (IFPUG Function Point Analysis) measurement plugin. These models represent the measurement output — the result of applying deterministic counting rules to the Canonical Functional Model (F06). They are consumed by Export Layer (F10) and Publisher (F11) plugins.

## Entity Definitions

### APFMeasurementResult

Top-level container for a complete APF function point measurement.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `str` | Unique pipeline run identifier, sourced from pipeline context |
| `cfm_run_id` | `str` | Source Canonical Functional Model run_id |
| `rule_pack_id` | `Optional[str]` | Identifier of the applied Rule Pack (null if default rules used) |
| `measured_functions` | `list[MeasuredFunction]` | All measured functions with classifications and evidence |
| `summary` | `MeasurementSummary` | Aggregated counts, weights, and totals |
| `explanations` | `list[MeasurementExplanation]` | Per-function explanations with evidence trails |
| `warnings` | `list[MeasurementWarning]` | Non-fatal issues encountered during measurement |
| `errors` | `list[MeasurementError]` | Fatal errors that prevented complete measurement |
| `measured_at` | `datetime` | Timestamp of measurement completion |

**Validation Rules**:
- If `errors` is non-empty, `summary.total_ufp` must be null (no partial results on error)
- All `measured_function[i].id` values must be unique
- `summary.total_function_count` must equal `len(measured_functions)`

**State Transitions**:
- `Pending` (initial) → `Complete` (after measurement finishes) — no partial states; if interrupted, result is discarded

---

### MeasuredFunction

A single function point with its type classification, complexity, and contribution.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the measurement result |
| `name` | `str` | Function name, derived from originating CFM element |
| `function_type` | `FunctionType` | APF classification: `ILF`, `EIF`, `EI`, `EO`, `EQ` |
| `complexity` | `ComplexityRating` | Rating: `Low`, `Average`, `High` |
| `det_count` | `int` | Data Element Type count contributing to complexity |
| `ret_count` | `Optional[int]` | Record Element Type count (data functions only) |
| `ftr_count` | `Optional[int]` | File Types Referenced count (transactional functions only) |
| `ufp_weight` | `int` | Unadjusted Function Point weight for this function |
| `cfm_element_id` | `str` | ID of the originating CFM element |
| `cfm_element_type` | `str` | CFM entity type that originated this function (`DataGroup`, `Operation`, etc.) |
| `evidence_refs` | `list[EvidenceRef]` | Evidence trail back to specification fragments |
| `rule_applied` | `Optional[str]` | Identifier of the specific counting rule applied (for Rule Pack overrides) |

**Validation Rules**:
- `function_type` determines which of `ret_count`/`ftr_count` is required: data functions (ILF, EIF) must have `ret_count`; transactional (EI, EO, EQ) must have `ftr_count`
- `ufp_weight` must match the IFPUG weight table value for the given `function_type` and `complexity` (unless overridden by a Rule Pack)
- `det_count` must be >= 1

---

### MeasurementSummary

Aggregated totals and breakdowns.

| Field | Type | Description |
|-------|------|-------------|
| `total_function_count` | `int` | Total number of measured functions |
| `total_ufp` | `int` | Total Unadjusted Function Points |
| `adjusted_fp` | `Optional[int]` | Value Adjusted Function Points (null if VAF not applied) |
| `vaf` | `Optional[float]` | Value Adjustment Factor (null if not applied) |
| `by_type` | `dict[FunctionType, TypeBreakdown]` | Breakdown of counts and UFPs per function type |
| `by_complexity` | `dict[ComplexityRating, int]` | Count of functions per complexity level |
| `complexity_distribution` | `list[ComplexityDistributionRow]` | Full matrix: function type × complexity → count + UFP |

---

### TypeBreakdown

Count and UFP subtotal for a single function type.

| Field | Type | Description |
|-------|------|-------------|
| `count` | `int` | Number of functions of this type |
| `total_ufp` | `int` | Sum of UFP weights for this type |

---

### ComplexityDistributionRow

A single cell in the function type × complexity matrix.

| Field | Type | Description |
|-------|------|-------------|
| `function_type` | `FunctionType` | ILF, EIF, EI, EO, or EQ |
| `complexity` | `ComplexityRating` | Low, Average, or High |
| `count` | `int` | Number of functions at this intersection |
| `ufp_per_function` | `int` | UFP weight per function (standard IFPUG value or Rule Pack override) |
| `total_ufp` | `int` | `count * ufp_per_function` |

---

### MeasurementExplanation

A human-readable explanation of how a specific function was measured.

| Field | Type | Description |
|-------|------|-------------|
| `function_id` | `str` | Reference to the MeasuredFunction |
| `cfm_element_id` | `str` | Originating CFM element |
| `cfm_element_name` | `str` | Name of the originating CFM element |
| `classification_reason` | `str` | Why this function was classified as its `function_type` (e.g., "DataGroup with data_type='internal' → ILF candidate") |
| `complexity_reason` | `str` | How complexity was determined (e.g., "4 DETs × 2 RETs → Low complexity per IFPUG matrix") |
| `rule_exceptions` | `list[str]` | Any Rule Pack overrides applied to this function |
| `evidence_chain` | `list[str]` | Ordered list of trace steps: specification section → evidence graph node → CFM element → measured function |

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

### FunctionType

```python
Literal["ILF", "EIF", "EI", "EO", "EQ"]
```

### ComplexityRating

```python
Literal["Low", "Average", "High"]
```

## Classification Mapping

CFM entities are classified to APF function types using these deterministic rules:

| CFM Element Type | CFM Attribute Condition | APF Function Type |
|-----------------|------------------------|-------------------|
| `DataGroup` | `data_type == "internal"` | ILF (Internal Logical File) |
| `DataGroup` | `data_type == "external"` | EIF (External Interface File) |
| `DataGroup` | `data_type == "shared"` | ILF (treated as internal for APF purposes) |
| `Operation` | direction = input (creates/updates data) | EI (External Input) |
| `Operation` | direction = output (presents data) | EO (External Output) |
| `Operation` | direction = query (retrieves data only) | EQ (External Inquiry) |

**DET Derivation**:
- Data functions (ILF, EIF): DET count = number of fields/attributes in the DataGroup
- Transactional functions (EI, EO, EQ): DET count = number of distinct data fields crossed by the operation

**RET Derivation** (data functions only):
- RET count = number of logical sub-groups within the DataGroup

**FTR Derivation** (transactional functions only):
- FTR count = number of distinct DataGroups referenced by the Operation's parent FunctionalProcess

## Immutability

Once constructed, `APFMeasurementResult` is immutable. This guarantees:
- Deterministic export: identical result → identical export output
- Audit trail: measurement as-produced is preserved for verification
- Thread safety: concurrent consumers (export, publish) read without synchronization
