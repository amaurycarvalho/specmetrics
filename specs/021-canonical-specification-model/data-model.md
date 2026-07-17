# Data Model: Canonical Specification Model

## Overview

All canonical entities inherit from `CsmElement` (base). The `CanonicalSpecificationModel` is the immutable top-level container. Entities are stored in keyed dictionaries keyed by UUID string, enabling O(1) lookup by identity.

## CsmElement (Base)

```python
class CsmElement(BaseModel):
    id: str                                  # UUID v4 string
    description: str                         # Semantic content
    evidence_references: list[EvidenceRef]   # Provenance links
    status: Literal["active", "superseded"]  # Lifecycle state
```

**Validation rules**:
- `id` must be a valid UUID v4 string
- `description` must be non-empty
- `evidence_references` must contain at least one entry (enforced at builder level)
- `status` defaults to `"active"`

---

## CanonicalSpecificationModel (Root)

```python
class CanonicalSpecificationModel(BaseModel):
    model_config = {"frozen": True}

    run_id: str
    specification_activities: dict[str, SpecificationActivity] = {}
    decisions: dict[str, Decision] = {}
    assumptions: dict[str, Assumption] = {}
    constraints: dict[str, Constraint] = {}
    risks: dict[str, Risk] = {}
    open_questions: dict[str, OpenQuestion] = {}
    acceptance_criteria: dict[str, AcceptanceCriterion] = {}
    glossary_terms: dict[str, GlossaryTerm] = {}
    references: dict[str, Reference] = {}
    metadata: BuildMetadata
    evidence_graph_ref: str = ""
```

**Validation rules**:
- All collections are immutable (enforced by `frozen=True`)
- `run_id` must match the source EvidenceGraph's `run_id`

### Query interface

```python
def get_element(self, element_id: str) -> CsmElement | None
def get_elements(self, category: str) -> dict[str, CsmElement]
def get_elements_by_evidence(self, document_id: str) -> list[CsmElement]
def trace_evidence(self, element_id: str) -> list[EvidenceRef] | None
```

---

## SpecificationActivity

Inherits: `CsmElement`

```python
class SpecificationActivity(CsmElement):
    activity_type: Literal[
        "exploration", "clarification", "refinement",
        "review", "validation"
    ]
    activity_status: Literal["open", "in_progress", "completed", "superseded"]
    linked_decisions: list[str] = []       # UUID references
    linked_questions: list[str] = []       # UUID references
    linked_assumptions: list[str] = []     # UUID references
    linked_constraints: list[str] = []     # UUID references
    linked_risks: list[str] = []           # UUID references
    linked_acceptance_criteria: list[str] = []  # UUID references
```

**Validation rules**:
- `activity_type` is required (no default — must be classified)
- `activity_status` defaults to `"completed"` (since activities are recorded after the fact)
- Linked field values must reference valid UUIDs in the respective collection (enforced at build time)

---

## Decision

Inherits: `CsmElement`

```python
class Decision(CsmElement):
    rationale: str = ""
    alternatives: list[str] = []
    timestamp: str = ""  # ISO 8601 datetime string
```

---

## Assumption

Inherits: `CsmElement`

```python
class Assumption(CsmElement):
    validated_date: str | None = None  # ISO 8601 date; None if unvalidated
```

---

## Constraint

Inherits: `CsmElement`

```python
class Constraint(CsmElement):
    constraint_type: Literal["regulatory", "technical", "organizational"]
    source: str = ""
```

---

## Risk

Inherits: `CsmElement`

```python
class Risk(CsmElement):
    probability: str = ""     # e.g., "low", "medium", "high"
    impact: str = ""          # e.g., "low", "medium", "high"
    mitigation: str = ""
```

---

## OpenQuestion

Inherits: `CsmElement`

```python
class OpenQuestion(CsmElement):
    resolved: bool = False
    resolution: str = ""
```

---

## AcceptanceCriterion

Inherits: `CsmElement`

```python
class AcceptanceCriterion(CsmElement):
    verification_method: Literal["test", "review", "inspection"] = "test"
```

---

## GlossaryTerm

Inherits: `CsmElement`

```python
class GlossaryTerm(CsmElement):
    aliases: list[str] = []
```

---

## Reference (Fallback)

Inherits: `CsmElement`

```python
class Reference(CsmElement):
    original_label: str = ""   # Framework-specific label if any
```

For elements that cannot be classified into any canonical category. Preserves original text to avoid information loss (per FR-014).

---

## BuildMetadata

```python
class BuildMetadata(BaseModel):
    run_id: str
    build_duration_ms: int = 0
    element_counts: dict[str, int] = {}
    total_input_nodes: int = 0
    unclassified_count: int = 0
    classification_conflicts: list[ClassificationConflict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

---

## Entity Relationships

```
EvidenceGraph (input)
    │
    ├── classify_node(node) → category
    │
    ▼
CanonicalSpecificationModel
    ├── specification_activities  ←→ linked_decisions, linked_questions, etc.
    ├── decisions                 (UUID references to related entities)
    ├── assumptions
    ├── constraints
    ├── risks
    ├── open_questions
    ├── acceptance_criteria
    ├── glossary_terms
    └── references                (fallback)
        │
        ▼
    BuildMetadata
        ├── element_counts
        ├── classification_conflicts
        └── unclassified_count
```

Each entity is stored by its UUID string key. Cross-references between entities (e.g., an activity linking to its decisions) are stored as lists of UUID strings. The query interface resolves these on demand.

---

## State Transitions

| Entity | Status Values | Transitions |
|--------|--------------|-------------|
| CsmElement (base) | active, superseded | active → superseded |
| SpecificationActivity | open, in_progress, completed, superseded | open → in_progress → completed → superseded; completed → superseded |

All other entities follow the base `CsmElement.status` lifecycle (active → superseded). The CSM itself is immutable — status transitions represent updated versions of an element, not in-place mutation.
