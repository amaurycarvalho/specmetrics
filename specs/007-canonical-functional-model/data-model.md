# Data Model: Canonical Functional Model

## Overview

The Canonical Functional Model (CFM) is the framework-independent representation of functional knowledge extracted from software specifications. It is the output of the CFM Builder pipeline stage (F06) and the sole input contract for downstream measurement engines (F07), rule engines (F09), and other consumers.

## Entity Definitions

### CanonicalFunctionalModel

The top-level immutable container for all normalized functional knowledge.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `str` | Unique pipeline run identifier, sourced from EvidenceGraph |
| `actors` | `dict[str, Actor]` | Actors indexed by unique ID |
| `functional_processes` | `dict[str, FunctionalProcess]` | Functional processes indexed by unique ID |
| `business_rules` | `dict[str, BusinessRule]` | Business rules indexed by unique ID |
| `data_groups` | `dict[str, DataGroup]` | Data groups indexed by unique ID |
| `relationships` | `list[Relationship]` | Ordered list of relationships between CFM elements |
| `operations` | `dict[str, Operation]` | Operations indexed by unique ID |
| `unclassified` | `dict[str, UnclassifiedElement]` | Elements that could not be classified into standard categories |
| `metadata` | `BuildMetadata` | Diagnostic information about the CFM build |
| `evidence_graph_ref` | `str` | Reference to the source EvidenceGraph run_id |

**Validation Rules**:
- At least one of `actors`, `functional_processes`, `business_rules`, `data_groups` must be non-empty (or `unclassified` if no elements could be classified)
- Foreign key references in `relationships` must point to existing element IDs
- Immutable after construction — no setter methods exposed

**State Transitions**:
- `Empty` (initial, zero elements) → `Built` (after `build()` completes) — no further transitions

---

### Actor

A person, system, or role that performs or initiates functional processes.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the CFM |
| `name` | `str` | Actor name extracted from specification |
| `actor_type` | `ActorType` | Classification: `person`, `system`, `role` |
| `evidence` | `EvidenceRef` | Reference to originating evidence graph node |
| `metadata` | `dict[str, str]` | Optional additional attributes |

---

### FunctionalProcess

A cohesive unit of behavior that delivers value to an Actor.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the CFM |
| `name` | `str` | Process name extracted from specification |
| `description` | `str` | Brief description of the process purpose |
| `actor_ids` | `list[str]` | References to Actor IDs that participate in this process |
| `operation_ids` | `list[str]` | Ordered list of Operation IDs that compose this process |
| `data_group_ids` | `list[str]` | References to Data Group IDs that this process creates/reads/updates/deletes |
| `evidence` | `EvidenceRef` | Reference to originating evidence graph node |
| `metadata` | `dict[str, str]` | Optional additional attributes |

**Validation Rules**:
- At least one `actor_id` must reference an existing Actor
- All `operation_ids` must reference existing Operations
- All `data_group_ids` must reference existing DataGroups

---

### BusinessRule

A policy, constraint, or condition that governs how a Functional Process operates.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the CFM |
| `name` | `str` | Rule name extracted from specification |
| `description` | `str` | Full rule text or description |
| `rule_type` | `RuleType` | Classification: `constraint`, `condition`, `policy`, `derivation` |
| `related_process_ids` | `list[str]` | References to FunctionalProcess IDs this rule governs |
| `evidence` | `EvidenceRef` | Reference to originating evidence graph node |
| `metadata` | `dict[str, str]` | Optional additional attributes |

---

### DataGroup

A logical grouping of related data entities that a Functional Process creates, reads, updates, or deletes.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the CFM |
| `name` | `str` | Data group name extracted from specification |
| `description` | `str` | Brief description of the data represented |
| `data_type` | `DataType` | Classification: `internal`, `external`, `shared` |
| `related_process_ids` | `list[str]` | References to FunctionalProcess IDs that use this data |
| `evidence` | `EvidenceRef` | Reference to originating evidence graph node |
| `metadata` | `dict[str, str]` | Optional additional attributes |

---

### Relationship

A directed association between two CFM elements.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the CFM |
| `source_id` | `str` | Source element ID |
| `target_id` | `str` | Target element ID |
| `relationship_type` | `RelationshipType` | Classification: `triggers`, `composed_of`, `governs`, `uses`, `communicates_with` |
| `evidence` | `EvidenceRef` | Reference to originating evidence graph edge |
| `metadata` | `dict[str, str]` | Optional additional attributes |

**Validation Rules**:
- `source_id` and `target_id` must reference existing CFM elements (any entity type)
- Self-referencing relationships are allowed only for specific types (`composed_of` for hierarchical processes)

---

### Operation

A specific action within a Functional Process. Atomic unit of behavior.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the CFM |
| `name` | `str` | Operation name extracted from specification |
| `description` | `str` | Brief description of the action |
| `parent_process_id` | `str` | Reference to the parent FunctionalProcess ID |
| `evidence` | `EvidenceRef` | Reference to originating evidence graph node |
| `metadata` | `dict[str, str]` | Optional additional attributes |

---

### UnclassifiedElement

An evidence graph element that could not be mapped to any standard CFM category.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier within the CFM |
| `original_type` | `str` | Original semantic type from evidence graph |
| `content` | `str` | Original element content |
| `evidence` | `EvidenceRef` | Reference to originating evidence graph node |
| `metadata` | `dict[str, str]` | Optional additional attributes |

---

### BuildMetadata

Diagnostic information about a CFM build.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `str` | Pipeline run identifier |
| `build_duration_ms` | `int` | Time taken to build the CFM |
| `element_counts` | `dict[str, int]` | Count per category: actors, functional_processes, business_rules, data_groups, relationships, operations, unclassified |
| `total_input_nodes` | `int` | Number of nodes in the source evidence graph |
| `unclassified_count` | `int` | Number of elements that could not be classified |
| `conflicts` | `list[ClassificationConflict]` | Classification conflicts detected during build |
| `created_at` | `datetime` | Timestamp of CFM build completion |

---

### EvidenceRef

Reference to an evidence graph node, preserving full provenance.

| Field | Type | Description |
|-------|------|-------------|
| `graph_node_id` | `str` | ID of the source node in the evidence graph |
| `document_id` | `str` | Originating document identifier |
| `section_id` | `Optional[str]` | Section within the document (if applicable) |
| `text` | `str` | Source text fragment |

---

### ClassificationConflict

Records a conflict detected during element classification.

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | `str` | Evidence graph node ID that caused the conflict |
| `competing_categories` | `list[str]` | Categories the node matched |
| `resolved_category` | `str` | Category selected by priority heuristic |
| `reason` | `str` | Explanation of the resolution |

## Enumerations

### ActorType

```python
Literal["person", "system", "role"]
```

### RuleType

```python
Literal["constraint", "condition", "policy", "derivation"]
```

### DataType

```python
Literal["internal", "external", "shared"]
```

### RelationshipType

```python
Literal["triggers", "composed_of", "governs", "uses", "communicates_with"]
```

## Classification Mapping

Evidence graph nodes with `node_type="extracted_element"` are classified as follows:

| Evidence Graph `semantic_type` | CFM Category | Notes |
|-------------------------------|--------------|-------|
| `fact` | `BusinessRule` or `Operation` | Disambiguated by relationship context: connected to a process via `composed_of` edge → Operation; standalone → BusinessRule |
| `entity` — person/role name | `Actor` | Named entity recognized as a person or organizational role |
| `entity` — data/concept name | `DataGroup` | Named entity recognized as a data concept |
| `relationship` | `Relationship` | Preserves edge direction and type metadata |
| `operation` | `Operation` | Direct mapping |

**Priority Heuristic** (for conflicting classifications):
1. `BusinessRule` > `Operation` (rules take precedence)
2. `FunctionalProcess` > `Operation` (processes take precedence)
3. If an element matches 3+ categories, it is flagged as a conflict and assigned the highest-priority match

## Immutability

Once constructed, the `CanonicalFunctionalModel` is immutable. Consumers receive a read-only view. This guarantees:
- Deterministic measurement: identical CFM → identical measurement results
- Thread safety: concurrent consumers read the same model without synchronization
- Auditability: the model as-built is preserved for historical analysis
