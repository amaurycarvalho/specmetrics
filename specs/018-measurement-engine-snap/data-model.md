# Data Model: SNAP Measurement Engine

## Overview

Data entities for the SNAP (Software Non-functional Assessment Process) measurement plugin. These models represent the assessment output — the result of applying deterministic assessment rules to the Canonical Functional Model (F06) enriched with semantic metadata. They are consumed by Export Layer (F10) and Publisher (F11) plugins.

## Entity Definitions

### SNAPMeasurementResult

Top-level container for a complete SNAP assessment.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `str` | Unique pipeline run identifier, sourced from pipeline context |
| `cfm_run_id` | `str` | Source Canonical Functional Model run_id |
| `rule_pack_id` | `Optional[str]` | Identifier of the applied Rule Pack (null if default rules used) |
| `categories` | `list[CategoryAssessment]` | Assessment results grouped by category |
| `assessed_items` | `list[AssessedItem]` | All individually assessed items with evidence |
| `summary` | `AssessmentSummary` | Aggregated counts and totals |
| `explanations` | `list[AssessmentExplanation]` | Per-item explanations with evidence trails |
| `warnings` | `list[AssessmentWarning]` | Non-fatal issues encountered during assessment |
| `errors` | `list[AssessmentError]` | Fatal errors that prevented complete assessment |
| `assessed_at` | `datetime` | Timestamp of assessment completion |

**Validation Rules**:
- If `errors` is non-empty, `summary.total_snap` must be null (no partial results on error)
- All `assessed_item[i].id` values must be unique
- `summary.total_item_count` must equal `len(assessed_items)`
- Every category in `categories` must have a non-empty `items` list

**State Transitions**:
- `Pending` (initial) → `Complete` (after assessment finishes) — no partial states; if interrupted, result is discarded

---

### CategoryAssessment

Assessment results for a single SNAP category.

| Field | Type | Description |
|-------|------|-------------|
| `category_id` | `str` | Unique identifier for the assessment category |
| `category_name` | `str` | Human-readable name (e.g., "Presentation", "Data Operations") |
| `category_version` | `str` | SemVer version of the category definition |
| `items` | `list[AssessedItem]` | Assessed items belonging to this category |
| `total_contribution` | `float` | Sum of individual item contributions in this category |

---

### AssessedItem

A single assessed SNAP item.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the assessment result |
| `name` | `str` | Item name, derived from originating CFM element |
| `category_id` | `str` | Assessment category this item belongs to |
| `contribution` | `float` | Fixed SNAP contribution value for this category |
| `cfm_element_id` | `str` | ID of the originating CFM element |
| `cfm_semantic_marker` | `str` | Semantic metadata marker that triggered assessment (e.g., `presentation_interface`, `data_operation`) |
| `evidence_refs` | `list[EvidenceRef]` | Evidence trail back to specification fragments |
| `rule_applied` | `Optional[str]` | Identifier of the specific assessment rule applied (for Rule Pack overrides) |
| `excluded` | `bool` | Whether this item was excluded by a Rule Pack (reported but not counted) |

**Validation Rules**:
- `category_id` must reference a valid assessment category
- `contribution` must be a positive number matching the fixed value for the category (unless overridden by Rule Pack)
- If `excluded` is True, `contribution` must be 0 and a warning must be emitted

---

### AssessmentSummary

Aggregated totals and breakdowns.

| Field | Type | Description |
|-------|------|-------------|
| `total_item_count` | `int` | Total number of assessed items (including excluded) |
| `total_active_count` | `int` | Number of items contributing to the SNAP total (excluding excluded) |
| `total_snap` | `float` | Total SNAP assessment value |
| `by_category` | `dict[str, CategoryBreakdown]` | Breakdown of counts and SNAP per category |

---

### CategoryBreakdown

Count and SNAP subtotal for a single assessment category.

| Field | Type | Description |
|-------|------|-------------|
| `item_count` | `int` | Number of assessed items in this category |
| `total_snap` | `float` | Sum of SNAP contributions for this category |

---

### AssessmentExplanation

A human-readable explanation of how a specific item was assessed.

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | `str` | Reference to the AssessedItem |
| `cfm_element_id` | `str` | Originating CFM element |
| `cfm_element_name` | `str` | Name of the originating CFM element |
| `identification_reason` | `str` | Why this element was identified (e.g., "CFM semantic marker='presentation_interface' → Presentation category") |
| `contribution_reason` | `str` | How the contribution value was determined (e.g., "Default SNAP weight for Presentation category") |
| `rule_exceptions` | `list[str]` | Any Rule Pack overrides applied to this item |
| `evidence_chain` | `list[str]` | Ordered list of trace steps: spec section → evidence graph → CFM element → assessed item |

---

### AssessmentWarning

Non-fatal issue encountered during assessment.

| Field | Type | Description |
|-------|------|-------------|
| `code` | `str` | Machine-readable warning code |
| `message` | `str` | Human-readable description |
| `cfm_element_id` | `Optional[str]` | Related CFM element (if applicable) |
| `details` | `Optional[dict[str, str]]` | Additional context |

---

### AssessmentError

Fatal error that prevents complete assessment.

| Field | Type | Description |
|-------|------|-------------|
| `code` | `str` | Machine-readable error code |
| `message` | `str` | Human-readable description |
| `cfm_element_id` | `Optional[str]` | Related CFM element (if applicable) |
| `recoverable` | `bool` | Whether assessment can continue with partial results |

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

## Assessment Categories

Assessment categories are loaded from versioned definitions. Default categories follow the IFPUG SNAP methodology:

| Category ID | Name | Description |
|-------------|------|-------------|
| `presentation` | Presentation | Interface presentation and formatting characteristics |
| `data_operations` | Data Operations | Data manipulation and transformation complexity |
| `operational_capabilities` | Operational Capabilities | Installation, configuration, and operational features |
| `technical_interaction` | Technical Interaction | Technical interface and integration complexity |

**Category Versioning**: Each category definition carries a SemVer string validated at engine load time (FR-015).

## Classification Mapping

CFM elements are classified to SNAP assessment categories using these deterministic rules:

| CFM Semantic Marker | Assessment Category |
|--------------------|-------------------|
| `presentation_interface` | Presentation |
| `formatting_rule` | Presentation |
| `data_operation` | Data Operations |
| `data_transform` | Data Operations |
| `operational_feature` | Operational Capabilities |
| `technical_interface` | Technical Interaction |
| `integration_point` | Technical Interaction |

**Duplicate Merging**:
- Duplicates are identified by CFM node ID AND content fingerprint (SHA-256 of `document_id`, `section_id`, `text`, `semantic_type`)
- Matching duplicates are merged into a single AssessedItem (only one contributes to total SNAP)
- A warning is emitted for each merged duplicate

## Immutability

Once constructed, `SNAPMeasurementResult` is immutable. This guarantees:
- Deterministic export: identical result → identical export output
- Audit trail: assessment as-produced is preserved for verification
- Thread safety: concurrent consumers (export, publish) read without synchronization
