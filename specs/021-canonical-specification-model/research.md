# Research: Canonical Specification Model Builder

## 1. EvidenceGraph Input Contract

**Decision**: Consume the existing `EvidenceGraph` (defined in `specmetrics/kernel/evidence_graph.py`) — same graph that feeds the CFM Builder.

**Rationale**: The evidence graph already contains all node types (`extracted_element`, `evidence`) with semantic type annotations (`fact`, `entity`, `relationship`, `operation`). For CSM, we filter nodes that carry specification-process semantics (questions, decisions, assumptions, constraints, risks, glossary terms, acceptance criteria, activities) rather than functional semantics (actors, business rules, data groups).

**Input schema**:
- `GraphNode.node_type` = `"extracted_element"` for specification content
- `GraphNode.semantic_type` — one of `"fact"`, `"entity"`, `"relationship"`, `"operation"`
- `GraphNode.text` — raw text from the specification
- `GraphNode.document_id` / `section_id` — provenance context
- `GraphEdge` — connects elements with `"derived_from"`, `"references"`, `"composed_of"` types

**Alternatives considered**: None — the existing EvidenceGraph is the canonical pipeline input.

---

## 2. Classification Strategy: CSM vs CFM

**Decision**: Both CSM and CFM consume the same EvidenceGraph, but apply different classifiers. The CSM classifier detects *specification-process semantics*; the CFM classifier detects *functional semantics*. They run as independent stages.

**Rationale**: The semantic extraction stage already annotates nodes with properties that distinguish functional from specification-process content. We inspect node content patterns (questions, decisions, constraints, glossary-term-like text) and edge relationships to determine the CSM category.

**Classification rules**:
- **Decision**: Text matches decision patterns (`decided|chosen|selected|agreed|resolved`, past-tense actionable statements)
- **Assumption**: Text matches assumption patterns (`assume|assumed|presume|taken as true|we believe`)
- **Constraint**: Text matches constraint patterns (`must|shall|required|limited|cannot|restricted|only`)
- **Risk**: Text matches risk patterns (`risk|uncertainty|concern|might|potential issue|if/when`)
- **Open Question**: Text ends with `?` or matches question patterns (`unresolved|needs decision|TBD|open question`)
- **Acceptance Criterion**: Text matches acceptance patterns (`given|when|then|verify|validated|acceptance`)
- **Glossary Term**: Text is short, capitalized, definition-like (single concept + description)
- **Specification Activity**: Text matches activity patterns (`explore|clarify|refine|review|validate` plus temporal context from edges)
- **References (fallback)**: No confident match — preserve as-is

**Alternatives considered**: Single classifier with unified categories — rejected because functional and spec-process semantics serve different downstream consumers and mixing them violates separation of concerns.

---

## 3. SpecificationActivity Type Detection

**Decision**: Detect activity type from node text content and surrounding graph context (neighboring nodes, edge metadata).

**Rationale**: The evidence graph does not have a dedicated "activity_type" field. Activities are inferred from:
- **Exploration**: Text mentions discovery, research, investigation, alternatives considered
- **Clarification**: Text mentions resolution of ambiguity, answer to a question, elaboration
- **Refinement**: Text mentions restructuring, rewriting, improving clarity
- **Review**: Text mentions evaluation, inspection, checklist, verification
- **Validation**: Text mentions confirmation, stakeholder sign-off, acceptance

**Heuristic**: If a node has outgoing edges of type `"derived_from"` to multiple other spec-process nodes, it's likely a higher-level activity that subsumes them.

**Alternatives considered**: Requiring explicit activity type annotation in the extraction stage — rejected because it increases extraction complexity. Pattern-based detection is sufficient for v0.1 with acceptable accuracy.

---

## 4. CSM vs CFM Integration

**Decision**: CSM and CFM are independent stages both subscribing to `EVIDENCE_GRAPH_BUILT`. They run in parallel (within the same event-driven pipeline, both are handlers for the same event type).

**Rationale**: Both models consume the same EvidenceGraph but produce different outputs. Zero coupling between them. The PipelineEngine already supports multiple handlers per event type via HandlerRegistry (one handler per event type currently, but the architecture can be extended).

**Pipeline ordering**: Both CSM Builder and CFM Builder run after the Evidence Graph stage. The PipelineEngine dispatches to both handlers sequentially (order doesn't matter since they're independent). Both update separate fields on PipelineContext.

**New PipelineContext fields**: `canonical_spec_model: Optional[Any] = None`

**New EventType**: `CANONICAL_SPECIFICATION_MODEL_BUILT = "canonical_specification_model_built"`

**CANONICAL_EVENT_ORDER update**: Add `CANONICAL_SPECIFICATION_MODEL_BUILT` after `EVIDENCE_GRAPH_BUILT`.

**Alternatives considered**: Chaining CSM after CFM — rejected because there's no dependency between them and parallel execution enables independent evolution.

---

## 5. Evidence Node Processing

**Decision**: Process both `"extracted_element"` and `"evidence"` node types. Evidence nodes carry raw specification text with document/section context but no semantic type. They serve as provenance anchors for extracted elements.

**Rationale**: The CSM must preserve full provenance (FR-002, FR-003). Evidence nodes are the traceability mechanism. Each CsmElement stores `evidence_references: list[EvidenceRef]` linking to the source evidence nodes.

**Processing flow**:
1. Iterate all `extracted_element` nodes → classify into CSM categories → create entities
2. For each entity, collect associated evidence nodes via `"derived_from"` or `"references"` edges → populate `evidence_references`

---

## 6. Serialization & Immutability

**Decision**: Pydantic `model_config = {"frozen": True}` on the root model, JSON serialization via `model_dump_json()`.

**Rationale**: Matches the existing CFM pattern. JSON is the standard debugging format. Pydantic frozen models enforce immutability at the language level.

---

## 7. Performance Strategy

**Decision**: Single-pass iteration over the evidence graph with O(n) classification. No graph-wide traversals during initial build.

**Rationale**: SC-001 requires 500 elements in under 3 seconds. O(n) classification with regex-based pattern matching comfortably meets this target. Relationship traversal (linking activities to decisions/questions/assumptions) uses adjacency lookups via the edge list, which is O(m) for m edges.

**Benchmark baseline**: ~50μs per node for classification + entity construction → 500 nodes in ~25ms (orders of magnitude below the 3-second target).
