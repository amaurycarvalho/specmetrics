# Research: Populate Stage Entities on Run Artifacts

## Decision: How to carry per-stage entity data to serialization

**Decision**: Add `stage_entities: dict[str, list[dict]]` field to `PipelineResult`.

**Rationale**: `_serialize_stage_data()` receives only `PipelineResult`. The rich entity data (documents, extracted elements, graph nodes, CSM/CFM entities) exists on `PipelineContext` but is not exposed through `PipelineResult`. Adding per-stage entity fields directly to `PipelineResult` would require 8 new fields. A single `stage_entities` dict keyed by stage name is cleaner and extensible.

**Alternatives considered**:
1. Pass `PipelineContext` to `_serialize_stage_data()` — breaks current abstraction boundary; `save_run_artifacts` currently only receives `PipelineResult`.
2. Read from persisted files (evidence_graphs JSONL) at serialization time — redundant I/O, couples serialization to graph store format.
3. Individual fields per stage (e.g., `discovered_docs`, `extracted_elements`) — verbose, not future-proof for new stages.

**Implementation**:
- In `PipelineOrchestrator.execute()`, after `_build_stage_details()` and before constructing `PipelineResult`, build the entity dict from `ctx` data.
- Pass it as `stage_entities=` to `PipelineResult`.
- `_serialize_stage_data()` reads from `result.stage_entities[sd.name]` instead of only checking `result.metric_results`.

---

## Decision: How to add `run_artifacts.max_entities_per_stage` config key

**Decision**: Add `RunArtifactsSettings` to `CoreConfig` in `schema.py`.

**Rationale**: The existing `ConfigurationSystem` in `specmetrics/infrastructure/config/schema.py` uses Pydantic models. Adding a new nested settings class follows the existing pattern (`PipelineSettings`, `LoggingSettings`, `SecuritySettings`). The key will be `run_artifacts.max_entities_per_stage` in the flattened config.

**Alternatives considered**:
1. Add to existing `PipelineSettings` — semantically different (pipeline execution vs artifact serialization).
2. Environment variable only — not consistent with project's config approach.
3. CLI flag only — user wants config.yml persistence.

**Implementation**:
```python
class RunArtifactsSettings(BaseModel):
    max_entities_per_stage: int = 5000
    model_config = {"extra": "forbid"}
```

Nested in `CoreConfig`:
```python
class CoreConfig(BaseModel):
    pipeline: PipelineSettings = PipelineSettings()
    logging: LoggingSettings = LoggingSettings()
    security: SecuritySettings = SecuritySettings()
    run_artifacts: RunArtifactsSettings = RunArtifactsSettings()
```

---

## Decision: How to access config from `save_run_artifacts`

**Decision**: Pass the config value as a parameter through the call chain.

**Rationale**: `save_run_artifacts()` currently receives `(project_path, measure_id, result)`. Adding an optional `max_entities_per_stage: int = 5000` parameter is the minimal change. The orchestrator already has access to the `ConfigurationSystem` instance.

**Alternatives considered**:
1. Singleton config accessor — adds hidden dependency.
2. Store in `PipelineResult` — mixes config with output data.

**Call chain**: `run_measure()` (cli/measure.py) → `orchestrator.execute()` → returns `PipelineResult` → `save_run_artifacts()`. The orchestrator loads config, so it can pass the value through.

---

## Decision: How to serialize evidence references

**Decision**: Preserve the canonical model's native evidence structure — CSM entities use `evidence_references` (list, plural) and CFM entities use `evidence` (single, singular) — and serialize them directly via `model_dump()`.

**Rationale**: FR-005 and FR-006 specify "canonical fields" for each entity type. CSM entities have `evidence_references: list[EvidenceRef]` while CFM entities have `evidence: EvidenceRef` (singular). Normalizing to a single format would add unnecessary transformation and could lose data (CSM entities may have multiple evidence refs per entity). Using Pydantic's built-in `model_dump(mode="json")` is the simplest, most maintainable approach.

**Implementation**: For CSM and CFM stages, iterate over each entity category dict, call `model_dump(mode="json")` on each entity, and truncate `description`/`text` fields to 200 chars.

---

## Decision: Measure stage breakdown enrichment

**Decision**: For the measure stage, include key metrics' breakdown data alongside the existing metric totals.

**Rationale**: FR-008 requires breakdown per complexity-level or function-type for each metric that supports it. The `measurement_result` dict in `ctx` already contains breakdown data for FPA and other methods. This data is currently only used in `_extract_measurement()` for the legacy `MeasurementResult` but is available in the raw dict.

**Implementation**: In `_build_stage_entities()`, for the measure stage, extract breakdown from `ctx.measurement_result` dict. Structure per metric: `{ "metric": "...", "total": N, "status": "...", "duration_ms": N, "breakdown": {...} }`.

---

## Decision: Document entity serialization for discover stage

**Decision**: Serialize `Document` objects using a manually constructed dict with `id`, `document_type`, and `path` fields.

**Rationale**: `Document` is a dataclass (not Pydantic), so `model_dump()` is not available. The spec requires only 3 fields: `id`, `document_type`, and `path`. Direct dict construction is the simplest approach.

**Implementation**: For each doc in `adapter_result["documents"]`, produce `{"id": doc.id, "document_type": doc.document_type, "path": str(doc.path)}`.

---

## Decision: Graph stage entity serialization

**Decision**: Iterate over `ctx.evidence_graph` dict to produce node entities and a summary entity with edge_count.

**Rationale**: `ctx.evidence_graph` is a dict with `node_count`, `edge_count`, `run_id`, and optionally `nodes`/`edges` lists (already constructed during graph building). The evidence graph is also persisted to JSONL, but reading it again would be wasteful — the in-memory dict is available.

**Implementation**: If `ctx.evidence_graph` contains node detail (list of dicts), iterate and truncate `text` to 200 chars. Append a summary entity: `{"node_type": "graph_summary", "edge_count": N, "run_id": "..."}`.

---

## Decision: Rule stage entity serialization

**Decision**: Use CFM metadata which contains `applied_rules` and `vaf` after Rule Pack application.

**Rationale**: The Rule Pack Engine enriches the CFM in-place by modifying its `metadata.applied_rules` and `metadata.vaf`. These fields are available on `ctx.canonical_model.metadata` after the rule stage executes. No separate rule result tracking is needed.

**Implementation**: Read `ctx.canonical_model.metadata.applied_rules` for rule pack names and `ctx.canonical_model.metadata.vaf` for the Value Adjustment Factor. Structure: `{"rule_pack_name": "...", "description": "...", "version": "...", "entities_modified": N, "vaf_applied": float}`.
