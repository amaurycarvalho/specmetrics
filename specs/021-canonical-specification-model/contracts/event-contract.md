# Event Contract: CanonicalSpecificationModelBuilt

## Event Type

`EventType.CANONICAL_SPECIFICATION_MODEL_BUILT = "canonical_specification_model_built"`

## Publisher

`csm_builder_stage`

## Subscribed By

Downstream stages in `CANONICAL_EVENT_ORDER` that depend on specification-process knowledge:
- Future: Token Points measurement engine
- Future: Cognitive Points measurement engine
- Future: Specification quality analyzer

## Payload Schema

```python
@dataclass(frozen=True)
class CanonicalSpecificationModelBuiltPayload:
    run_id: str
    element_counts: dict[str, int]
    build_duration_ms: int
    total_input_nodes: int
    unclassified_count: int
    conflict_count: int
```

## PipelineContext Integration

Add field to `PipelineContext`:

```python
@dataclass(frozen=True)
class PipelineContext:
    ...
    canonical_spec_model: Optional[Any] = None
    ...
```

## CANONICAL_EVENT_ORDER Update

Insert `CANONICAL_SPECIFICATION_MODEL_BUILT` after `EVIDENCE_GRAPH_BUILT`:

```python
CANONICAL_EVENT_ORDER: list[EventType] = [
    EventType.REPOSITORY_LOADED,
    EventType.DOCUMENTS_DISCOVERED,
    EventType.DOCUMENTS_VALIDATED,
    EventType.SEMANTIC_EXTRACTION_COMPLETED,
    EventType.EVIDENCE_GRAPH_BUILT,                          # ← existing
    EventType.CANONICAL_SPECIFICATION_MODEL_BUILT,           # ← new
    EventType.CANONICAL_MODEL_BUILT,                         # ← existing
    EventType.RULE_PACK_APPLIED,
    EventType.MEASUREMENT_COMPLETED,
    EventType.EXPORT_COMPLETED,
    EventType.TELEMETRY_PUBLISHED,
]
```
