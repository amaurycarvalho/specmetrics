# Research: Explain Measurement

## Overview

Research findings and technology decisions for the Explain Measurement feature.

## Decisions

### Decision: Consume Evidence Graph and CFM via existing public interfaces

**Rationale**: The Evidence Graph (`kernel/evidence_graph.py`) already provides `GraphBackend` protocol with `traverse` and `query_nodes` methods, and the CFM (`kernel/cfm/`) exposes identified elements with their provenance. No new data sources are needed — the explanation service queries these existing structures.

**Alternatives considered**:
- Building a dedicated explanation store — duplicates data already in the Evidence Graph, violates DRY
- Embedding explanation logic in the Measurement Engine — violates Layer Independence (XIV)
- Deriving explanations from raw spec re-parsing — loses measurement-time context and Rule Pack application details

### Decision: Separate models for explanation output

**Rationale**: Spec FR-010 requires machine-readable structured output. Pydantic v2 models (MeasurementExplanation, MetricExplanation, EvidenceReference, AppliedRule, ExplanationComparison) provide schema validation, serialization to JSON, and self-documentation. These are distinct from the internal Evidence Graph and CFM models because they aggregate data across multiple sources for presentation.

**Alternatives considered**:
- Using Evidence Graph and CFM models directly — would leak internal implementation details into the output; violates information-hiding
- Plain dict output — no type safety, no validation, no documentation

### Decision: Evidence tracing via GraphBackend.traverse()

**Rationale**: The Evidence Graph `GraphBackend` protocol already supports bidirectional traversal (`forward`/`reverse`) with configurable depth. Tracing a metric element back to its source evidence is a reverse traversal from the CFM element node through `derived_from` edges to evidence nodes. No new graph operations needed.

**Alternatives considered**:
- Custom query engine — reinvents existing capability in `kernel/graph_query_engine.py`
- Direct NetworkX queries — couples explanation logic to the graph backend implementation

### Decision: Explanation formatters as plugin extension point

**Rationale**: FR-010 requires structured machine-readable output, and future UI integrations will need different formats. Using the existing plugin discovery mechanism (entry points) for formatters allows third-party output formats without modifying the core. Text and JSON formatters are built-in.

**Alternatives considered**:
- Hardcoded format functions — extensible only via core changes
- Single output format — violates FR-010's requirement for structured consumption by different consumers

### Decision: `specmetrics explain` CLI subcommand

**Rationale**: Aligns with existing CLI architecture (Typer-based, command-per-feature, e.g., `specmetrics validate`, `specmetrics measure`). The explain command accepts a measurement run ID or result file and optionally a metric filter.

**Alternatives considered**:
- Adding `--explain` flag to `specmetrics measure` — conflates measurement execution with explanation, makes CI/CD usage awkward
- Hidden behind an MCP-only interface — limits CLI users who don't use MCP

### Decision: Explanation comparisons compare two serialized MeasurementExplanation records

**Rationale**: FR-006 requires comparison across measurement runs. Persisting MeasurementExplanation output at measurement time (or generating it on demand) provides a stable comparison baseline. Comparison is purely structural (field-by-field diff with semantic awareness).

**Alternatives considered**:
- Re-running measurement twice — expensive, requires original specs to be unchanged
- Comparing raw Evidence Graphs — too low-level; would require reconstructing metric meaning from graph primitives

## Dependencies

### Existing (reuse)

| Dependency | Usage |
|---|---|
| Pydantic v2 | MeasurementExplanation, MetricExplanation, EvidenceReference, AppliedRule models |
| NetworkX / GraphBackend | Evidence graph traversal for evidence tracing |
| structlog | Structured explanation output |
| Typer | CLI command integration |
| pluggy / entry points | Formatter plugin discovery |

### New (if any)

No new external dependencies required. All explanation logic is custom, operating on existing infrastructure.

## Integration Points

| Interface | Direction | Purpose |
|---|---|---|
| CLI (`specmetrics explain`) | User → System | Request explanation for a measurement result |
| MCP (`explain_measurement` tool) | Agent → System | Request explanation programmatically |
| Evidence Graph (traverse) | System → Evidence Graph | Trace metrics to source evidence |
| CFM (element queries) | System → CFM | Get identified elements with classifications |
| Rule Pack records (applied rules) | System → Rule Store | Retrieve which rules affected which elements |
| stdout (structured output) | System → User | Text/JSON explanation report |
