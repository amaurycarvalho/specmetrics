# ADR-001: Architectural Decisions of SpecMetrics

**Date:** 2026-07-17

**Status:** Accepted

## Context

SpecMetrics is a software specification analysis and measurement tool capable of processing system specification documents, extracting semantic elements, building canonical functional models, and applying software engineering metrics (FPA, SFP, SNAP).

## Decision Drivers

- **Plugin extensibility** — support for multiple specification frameworks (OpenSpec, SpecKit) and measurement engines (FPA, SFP, SNAP)
- **Determinism** — same input must produce the same output regardless of environment
- **Intermediate immutability** — artifacts produced at each pipeline stage must not be altered retroactively
- **Traceability (provenance)** — every measurement result must be traceable to the original specification element
- **Pipeline composition** — the measurement process is a well-defined sequence of stages executed in deterministic order

## Architectural Decisions

### 1. Semantic Measurement Pipeline as Central Orchestrator

The pipeline is the architectural core. Each stage produces an immutable artifact stored in `PipelineContext`, which is passed forward. Stages execute in fixed order:

```
RepositoryLoaded → DocumentsDiscovered → SemanticExtractionCompleted →
EvidenceGraphBuilt → CanonicalModelBuilt → RulePackApplied →
MeasurementCompleted → ExportCompleted → TelemetryPublished
```

### 2. Plugin Discovery via Python Entry Points

Plugins are discovered via `Python Entry Points` under the `specmetrics.plugins` group. The registry validates API version compatibility (SemVer) at load time. Plugin errors do not crash the system — the stage fails gracefully.

### 3. Specification Adapter Interface

Each specification framework (OpenSpec, SpecKit) implements an adapter that:

- Discovers artifacts in the repository
- Normalizes them into a framework-agnostic `Document` model
- Preserves metadata (framework, domain, type, path)

Adapters **never interpret semantic meaning** — their responsibility ends at structural normalization.

### 4. Semantic Extraction with Provenance

Normalized documents are transformed into semantic elements (facts, entities, relationships, operations) via pluggable extraction providers. An LLM-assisted provider is included by default. Each extracted element maintains an `EvidenceReference` linking back to the source document and section.

### 5. Evidence Graph as Fact Store

Extracted elements are stored in a directed graph (NetworkX) with nodes (extracted elements + evidence fragments) and typed edges (`derived_from`, `references`, `composed_of`). Persistence uses JSONL files with atomic write guarantees.

### 6. Canonical Functional Model (CFM) with 6 Categories

The CFM is an immutable, framework-independent model with six categories: Actors, Functional Processes, Business Rules, Data Groups, Relationships, and Operations. Unclassifiable elements are preserved under "References". Classification conflicts are resolved by priority heuristic.

### 7. Measurement Engines as Deterministic Plugins

Each measurement engine (FPA, SFP, SNAP) is a separate plugin that consumes only the CFM. The FPA engine follows IFPUG CPM 4.3 with complexity matrices, DET/RET/FTR counting, and 14 General System Characteristics for VAF. SFP and SNAP are post-MVP.

### 8. Rule Pack Engine for Externalized Policies

Organization-specific measurement rules are externalized as declarative YAML files (no scripting) in the `.specmetrics/rules/` directory. Supports exclusions, complexity threshold overrides, VAF configuration, glossary overrides, and applied rule annotation.

### 9. Two Interaction Interfaces (CLI and MCP)

- **CLI** (Typer): commands `measure`, `plugins list`, `init`, `validate`, `export`, `publish`
- **MCP Server**: exposes capabilities as MCP tools via JSON-RPC 2.0 over stdio or SSE

Both interfaces use the same underlying pipeline orchestration.

### 10. Hierarchical Configuration System

Centralized configuration in `specmetrics.yml` with hierarchy: system < user < project < env vars < CLI args. Uses Pydantic Settings for validation. Supports YAML and JSON, sensitive value masking, and per-plugin configuration schemas.

### 11. Export Layer and OpenTelemetry Publisher

Measurement results can be exported to JSON, CSV, XML (built-in) or custom formats via plugins. The OpenTelemetry Publisher sends metrics via OTLP (gRPC/HTTP) with exponential backoff retry, without blocking the pipeline.

### 12. Validation as an Independent Stage

The validation pipeline (F14) checks semantic consistency before measurement: missing mandatory sections, unrecognized formats, constitutional compliance. It is a separate stage that feeds into the measurement pipeline without being part of it.

## Architectural Patterns

| Pattern                     | Application                                                       |
| --------------------------- | ----------------------------------------------------------------- |
| **Pipeline**                | Sequential stage orchestration with immutable context             |
| **Plugin**                  | Discovery via entry points, central registry, interface contracts |
| **Adapter**                 | Adapters normalize specifications into the canonical model        |
| **Strategy**                | Interchangeable extraction providers and measurement engines      |
| **Event Bus**               | In-process sync event bus for inter-stage communication           |
| **Repository**              | Evidence graph and export persistence on filesystem               |
| **Value Object**            | Immutable models (CFM, PipelineEvent)                             |
| **Builder**                 | CFM construction from the evidence graph                          |
| **Chain of Responsibility** | Validation pipeline with chained rules                            |

## Consequences

- Plugin-based architecture allows adding new specification frameworks and measurement engines without modifying the core
- Pipeline determinism guarantees measurement reproducibility
- Immutability and provenance enable full audit of results
- CLI/MCP separation allows use by both humans and AI agents
- Externalized rules via Rule Packs eliminate the need to change code for organizational policies
- The evidence graph as intermediate storage enables rich queries and full traceability
