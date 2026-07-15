# Implementation Plan: Evidence Graph Store

**Branch**: `006-evidence-graph-store` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-evidence-graph-store/spec.md`

## Summary

Build the Evidence Graph pipeline stage — the fourth stage in the SpecMetrics measurement pipeline. It receives `ExtractionResult` from Semantic Extraction (F04), constructs a directed provenance graph where every extracted element is a node traced to its source evidence, supports queries by document/type/provenance, provides persistence to disk, and enables incremental document-level updates. Output is consumed by the Canonical Functional Model layer (F06).

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: NetworkX (graph representation), Pydantic v2 (models), structlog (logging), LiteLLM (not directly — consumes F04 output)

**Storage**: File-based serialization (JSON/JSONL) — one file per pipeline run, identified by run ID

**Testing**: pytest (unit: graph operations, query engine, persistence; integration: pipeline stage wiring)

**Target Platform**: Linux, local execution (CLI + MCP Server)

**Project Type**: CLI + Library (hybrid — core library with CLI/MCP interfaces)

**Performance Goals**: Graph build <5s for 1,000 nodes / 500 edges; queries <100ms; persistence <10s for 10,000 nodes; incremental update <2s for 100-node replacement

**Constraints**: <200ms p95 query latency; <100MB memory for typical single-repo graphs; offline-capable (no external service dependency); deterministic rebuild (same input → same graph)

**Scale/Scope**: 10k nodes per graph; single repository per pipeline run; local development machine

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: I (Specification First), II (Specification as a Measurable Asset), V (Evidence First), VI (Explainability by Design), VII (Canonical Representation), XI (Observability as a Native Capability), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First: Primary input is ExtractionResult produced from specification documents — never reads source code.
- [x] Evidence First: Every graph node preserves its evidence reference. Evidence is a first-class node type. Provenance queries trace any measurement back to source text.
- [x] Canonical Representation: The graph uses a canonical node/edge model. Downstream (F06) consumes this model — never framework-specific extraction formats.
- [x] Plugin-Oriented: The graph engine is a core pipeline stage, not a plugin. Query/persistence backends MAY be pluggable in future iterations but are not required now.
- [x] Rule Externalization: No measurement policies are embedded in this stage — it is purely a data structure and provenance preserve.
- [x] Layer Independence: Consumes ExtractionResult from F04, produces EvidenceGraph for F06. No direct coupling between layers.
- [x] Open by Default: Graph schema is documented; persistence format is standard JSON/JSONL; query interface is defined by documented methods.

## Project Structure

### Documentation (this feature)

```text
specs/006-evidence-graph-store/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── evidence_graph.py        # EvidenceGraph data structure & operations
│   ├── evidence_graph_stage.py  # Pipeline event handler stage
│   ├── graph_query_engine.py    # Query interface
│   ├── graph_persistence.py     # Save/load/backup
│   └── events.py                # (adds EvidenceGraphBuilt event type)

tests/
├── unit/
│   ├── test_evidence_graph.py
│   ├── test_graph_query_engine.py
│   └── test_graph_persistence.py
└── integration/
    └── test_evidence_graph_pipeline.py
```

**Structure Decision**: Single Python package as per project convention. New files added under `specmetrics/kernel/` (core library) and `tests/` (unit + integration). No new subpackages needed — the evidence graph is a single pipeline stage implemented in <5 source files.

## Complexity Tracking

No violations. All Constitution checks pass without justification needed.
