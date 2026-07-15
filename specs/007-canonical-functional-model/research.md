# Research: Canonical Functional Model Builder

## Overview

No unresolved unknowns existed in the spec — the project constitution, existing codebase, and feature spec provided sufficient design guidance. This document confirms technology choices and documents integration patterns discovered during codebase exploration.

## Technology Decisions

### Domain Modeling: Pydantic v2

- **Decision**: Use Pydantic v2 `BaseModel` with `Field()` validators for all CFM entity definitions and `Literal` types for constrained choices
- **Rationale**: Pydantic v2 is the project-standard modeling library (per constitution). All existing models (`EvidenceGraph`, `GraphNode`, `ExtractedElement`, etc.) follow this pattern. It provides validation, serialization (`model_dump()`), and deserialization at zero additional dependency cost.
- **Alternatives considered**: Dataclasses (used for `PipelineEvent`/`PipelineContext` — less validation), `attrs` (not used in project)

### Pipeline Stage Pattern: Protocol-based EventHandler

- **Decision**: Implement CFM Builder as a class satisfying the `EventHandler` protocol with three properties (`handled_event_type`, `handler_id`, `stage_name`) and a `handle(event: PipelineEvent) -> PipelineContext` method
- **Rationale**: All existing stages (`ExtractionStage`, `EvidenceGraphStage`) follow this pattern. The `HandlerRegistry` expects this protocol. No base class inheritance is required but explicit properties are expected.
- **Alternatives considered**: Functional handlers (would break registry contract), inheritance from base class (project uses protocol, not ABC)

### Event Wiring: CANONICAL_MODEL_BUILT

- **Decision**: The CFM Builder handles `EventType.EVIDENCE_GRAPH_BUILT` and emits its output via `context.with_stage_output(field_name="canonical_model", value=payload)`
- **Rationale**: 
  - `EventType.CANONICAL_MODEL_BUILT` is already defined in `events.py`
  - `CANONICAL_EVENT_ORDER` in `pipeline_engine.py` already includes it after `EVIDENCE_GRAPH_BUILT`
  - `PipelineContext` already has `canonical_model: Optional[Any] = None`
  - The pipeline engine already creates events with `payload={}`, so stages read previous output from the context
- **Discovery**: The EvidenceGraphStage currently reads from `event.payload` (empty in engine) and writes to `context.evidence_graph` — the CFM Builder should read from `event.context.evidence_graph`

### Evidence Graph Data Access

- **Decision**: The CFM Builder receives evidence graph metadata (run_id, node_count, etc.) from `event.context.evidence_graph` and loads the full `EvidenceGraph` model from the persistence layer (GraphStore at `.evidence_graphs/{run_id}.jsonl`)
- **Rationale**: The EvidenceGraphStage persists the full graph to disk. The context only carries summary metadata. Loading from persistence ensures the CFM Builder works with the complete data and avoids duplicating graph data in memory via the context.
- **Alternative considered**: Store full `EvidenceGraph` in context (would increase memory pressure and couple context to a specific model type)
- **Alternative considered**: Pass `EvidenceGraph` directly in payload (pipeline engine currently passes empty payloads)

### Classification Strategy

- **Decision**: Evidence graph nodes with `node_type="extracted_element"` are classified by their `semantic_type` field:
  - `semantic_type="fact"` → `BusinessRule` or `Operation` (disambiguated by relationship context — facts connected to a process via `composed_of` edge → Operation, standalone → BusinessRule)
  - `semantic_type="entity"` → `Actor` (if named as person/role) or `DataGroup` (if named as data)
  - `semantic_type="relationship"` → `Relationship`
  - `semantic_type="operation"` → `Operation`
- **Rationale**: Uses existing semantic type information from the evidence graph without requiring re-analysis. Actor vs DataGroup disambiguation uses naming heuristics (person/role names vs data names).
- **Alternatives considered**: Pure type-based mapping (loses Actor/DataGroup distinction for entities), LLM-assisted classification (violates determinism principle IV)

## Integration Patterns

### CFM as Pipeline Contract

The CFM is the architectural boundary defined in Principle VII. All downstream measurement plugins consume the CFM — never framework-specific artifacts. The CFM interface must be:
- Stable (backward-compatible changes only)
- Framework-agnostic (no OpenSpec, SpecKit, or other SDD labels)
- Fully documented (so plugin developers can implement against it without reading internals)

### Relationship to Existing Code

| File | Impact |
|------|--------|
| `kernel/events.py` | `CANONICAL_MODEL_BUILT` already defined — no change |
| `kernel/pipeline_context.py` | `canonical_model` field already exists — no change |
| `kernel/pipeline_engine.py` | `CANONICAL_EVENT_ORDER` already includes `CANONICAL_MODEL_BUILT` — no change |
| `kernel/handler_registry.py` | New handler registration needed for CFM Builder stage |
| `kernel/evidence_graph.py` | CFM Builder imports `EvidenceGraph`, `GraphNode`, `GraphEdge` models |
| `kernel/graph_persistence.py` | CFM Builder uses `GraphStore.load()` to retrieve graph by run_id |

### Known Issues

- EvidenceGraphStage reads `event.payload.get("results", {})` but pipeline engine passes `payload={}` — the stage currently gets no data through the event. The CFM Builder should read from `event.context.evidence_graph` instead.
