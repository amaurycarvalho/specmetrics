# CSM Consumer Protocol

## Purpose

Define the stable public interface that downstream measurement engines (Token Points, Cognitive Points, quality analyzers) use to consume a `CanonicalSpecificationModel` without framework-specific dependencies.

## Python Protocol

```python
class CsmConsumer(Protocol):
    """Protocol for downstream consumers of CanonicalSpecificationModel.

    Any measurement engine that implements this protocol can consume a CSM
    without importing OpenSpec, SpecKit or any SDD-framework-specific module.
    """

    def consume(self, csm: CanonicalSpecificationModel) -> Any: ...
```

## Query Interface

The `CanonicalSpecificationModel` exposes the following methods for programmatic access:

```python
def get_element(self, element_id: str) -> CsmElement | None
    """Look up any element by its UUID."""

def get_elements(self, category: str) -> dict[str, CsmElement]
    """Enumerate all elements in a category.
    Valid categories: specification_activities, decisions, assumptions,
    constraints, risks, open_questions, acceptance_criteria,
    glossary_terms, references
    """

def get_elements_by_evidence(self, document_id: str) -> list[CsmElement]
    """Find all elements originating from a given document."""

def trace_evidence(self, element_id: str) -> list[EvidenceRef] | None
    """Get the full evidence chain for an element."""
```

## Serialization Contract

```python
csm.model_dump_json(indent=2)  # → str (JSON)
CanonicalSpecificationModel.model_validate_json(json_str)  # → CanonicalSpecificationModel
```

## Event Contract

The CSM Builder emits a `CanonicalSpecificationModelBuilt` event with payload:

```json
{
  "run_id": "uuid-string",
  "element_counts": {
    "specification_activities": 5,
    "decisions": 12,
    "assumptions": 8,
    "constraints": 3,
    "risks": 4,
    "open_questions": 6,
    "acceptance_criteria": 10,
    "glossary_terms": 15,
    "references": 2
  },
  "build_duration_ms": 42,
  "total_input_nodes": 75,
  "unclassified_count": 2,
  "conflict_count": 0
}
```

## Test Double

For unit testing downstream engines without building a real CSM:

```python
class FakeCsmConsumer:
    def __init__(self):
        self.consumed = None

    def consume(self, csm):
        self.consumed = csm
        return {"status": "ok", "element_count": len(csm.get_elements("decisions"))}
```
