# ADR-001: Architectural Decisions of SpecMetrics

**Date:** 2026-07-17

**Status:** Accepted

## Context

SpecMetrics is a software specification analysis and measurement tool capable of processing system specification documents, extracting semantic elements, building canonical functional and specification models, and applying a wide range of software engineering metrics (FPA, SFP, SNAP, Token Points, Cognitive Points, Story Points, T-Shirt Sizing, BCP).

## Decision Drivers

- **Plugin extensibility** — support for multiple specification frameworks (OpenSpec, SpecKit) and measurement engines (FPA, SFP, SNAP, Token Points, Cognitive Points, Story Points, T-Shirt Sizing, BCP)
- **Determinism** — same input must produce the same output regardless of environment (except BCP, which delegates to an external LLM-based SDK by design)
- **Intermediate immutability** — artifacts produced at each pipeline stage must not be altered retroactively
- **Traceability (provenance)** — every measurement result must be traceable to the original specification element
- **Pipeline composition** — the measurement process is a well-defined sequence of stages executed in deterministic order

## Architectural Decisions

### 1. Semantic Measurement Pipeline as Central Orchestrator

The pipeline is the architectural core. Each stage produces an immutable artifact stored in `PipelineContext`, which is passed forward. Stages execute in fixed order defined by `CANONICAL_EVENT_ORDER` in `pipeline_engine.py`:

```
RepositoryLoaded → DocumentsDiscovered → DocumentsValidated →
SemanticExtractionCompleted → EvidenceGraphBuilt →
CanonicalSpecificationModelBuilt → CanonicalModelBuilt →
RulePackApplied → MeasurementCompleted → TShirtClassificationCompleted →
ExportCompleted → TelemetryPublished
```

The pipeline engine iterates through registered event types, creating a `PipelineEvent` for each and dispatching via an in-process `EventBus`. Multiple handlers can subscribe to the same event type (e.g., both CFM and CSM builders registered for their respective events).

### 2. Plugin Discovery via Python Entry Points

Plugins are discovered via `Python Entry Points` under the `specmetrics.plugins` group. The registry validates API version compatibility (SemVer) at load time. Plugin errors do not crash the system — the stage fails gracefully.

Entry point groups:
- `specmetrics.plugins.measurement` — measurement engines
- `specmetrics.plugins.stage` — pipeline stage handlers
- `specmetrics.plugins.adapter` — specification framework adapters
- `specmetrics.plugins.rule_pack` — rule pack engine
- `specmetrics.plugins.semantic` — extraction providers
- `specmetrics.exporters` — export format plugins
- `specmetrics.publishers` — telemetry publishers

### 3. Specification Adapter Interface

Each specification framework (OpenSpec, SpecKit) implements an adapter that:

- Discovers artifacts in the repository
- Normalizes them into a framework-agnostic `Document` model
- Preserves metadata (framework, domain, type, path)

Adapters **never interpret semantic meaning** — their responsibility ends at structural normalization.

### 4. Semantic Extraction Engine as Unified Abstraction

Normalized documents are transformed into semantic elements (facts, entities, relationships, operations) through a unified `SemanticExtractionEngine` Protocol. A `SemanticEngineFactory` resolves the configured LLM provider to the correct engine implementation during pipeline initialization — the rest of the pipeline remains unaware of which engine is active.

| Configured Provider | Engine Implementation |
|---------------------|----------------------|
| `none` | `DeterministicSemanticEngine` |
| `chatgpt` / `claude` / `gemini` / `ollama` | `LiteLLMSemanticEngine` |

**Key properties:**
- Both engines produce identical `ExtractionResult` data models (FR-009)
- Every `ExtractedElement` carries an `EvidenceReference` with `document_id`, `section_id`, `text`, and (for deterministic) `rule_id`
- Element IDs are deterministic content-hash: `sha256(document_id + "::" + section + "::" + text)[:16]`
- Processing statistics include: documents processed, elements extracted, elements by type, duration, errors
- Engine selection occurs once per pipeline run and is transparent to downstream stages

### 5. Deterministic Semantic Engine with Rule-Based Extraction

The `DeterministicSemanticEngine` is the offline-capable implementation of the `SemanticExtractionEngine` Protocol. It performs extraction using only structural analysis — no network access, API keys, or AI services.

**Processing pipeline:**
```
Document → Markdown Parser → AST → Visitors → Rule Engine → Pattern Library → ExtractionResult
```

**AST Visitors** (one per token type):
- `HeadingVisitor` — heading hierarchy with known section detection (Actors, Business Rules, Constraints, etc.)
- `ListVisitor` — ordered/unordered list items with nesting
- `TableVisitor` — table rows and headers
- `ParagraphVisitor` — standalone paragraph text
- `CodeBlockVisitor` — fenced code blocks with language annotation
- `QuoteVisitor` — blockquote content
- `EmphasisVisitor` — bold/italic text spans
- `LinkVisitor` — hyperlinks and reference links

**Rule Engine** — two-phase: visitors produce `Observation` objects, then a rule engine matches observations against loaded rule packs to produce `ExtractedElement` instances. Rules are organized as external YAML files (not embedded in code), supporting the Rule Externalization principle.

**Rule Pack Schema** — each rule defines: `id`, `name`, `pattern` (keywords, heading text, or structure type), `type` (fact/entity/relationship/operation), `confidence` (0.0–1.0), and `priority` (1–100). When multiple rules match the same content, the highest priority wins; ties broken by rule ID lexicographic order.

**Built-in rule packs:**
- `default_rule_pack.yaml` — User Story, GWT, Requirements, Business Rules, Actors, Constraints, Assumptions, Decisions, Glossary Terms, Acceptance Criteria
- `openspec_rules.yaml` — OpenSpec framework conventions
- `speckit_rules.yaml` — SpecKit framework conventions

Framework-specific packs are auto-loaded based on `document.document_type` metadata.

### 6. Evidence Graph as Fact Store

Extracted elements are stored in a directed graph (NetworkX) with nodes (extracted elements + evidence fragments) and typed edges (`derived_from`, `references`, `composed_of`). Node IDs are deterministic SHA-256 fingerprints of `(document_id, section_id, text, semantic_type)`, enabling de-duplication across runs. Persistence uses JSONL files with atomic write guarantees.

### 7. Canonical Functional Model (CFM) with 6 Categories

The CFM is an immutable, framework-independent model with six categories: Actors, Functional Processes, Business Rules, Data Groups, Relationships, and Operations. Unclassifiable elements are preserved under "Unclassified". Classification conflicts are resolved by priority heuristic. The CFM builder subscribes to `EVIDENCE_GRAPH_BUILT` and produces a frozen `CanonicalFunctionalModel`.

### 8. Canonical Specification Model (CSM) with 9 Categories

Alongside the CFM, the CSM captures specification-specific knowledge: Specification Activities, Decisions, Assumptions, Constraints, Risks, Open Questions, Acceptance Criteria, Glossary Terms, and References. The CSM builder subscribes to `CANONICAL_SPECIFICATION_MODEL_BUILT` and produces a frozen `CanonicalSpecificationModel`. Every CSM element preserves complete evidence references and enforces UUID v4 validation on element IDs.

### 9. Measurement Engines as Deterministic Plugins

Each measurement engine is a separate plugin that consumes the CFM (and optionally the CSM) and produces a measurement result. All measurement engines follow the same pattern: a `Plugin` class with `measure()`, a `Handler` implementing `EventHandler`, and a `create_*_metadata()` factory.

| Engine | Input | Output | Deterministic |
|--------|-------|--------|---------------|
| **FPA** (IFPUG CPM 4.3) | CFM | Function Points | ✅ |
| **SFP** (Simple FP) | CFM | Simple Function Points | ✅ |
| **SNAP** (Non-functional) | CFM | SNAP Points | ✅ |
| **Token Points** | CFM + CSM | AI token cost estimate | ✅ |
| **Cognitive Points** | CFM + CSM | Human cognitive effort (Bloom taxonomy + Fibonacci) | ✅ |
| **Story Points** | CFM | Modified Fibonacci implementation effort (6-factor weighted sum) | ✅ |
| **T-Shirt Sizing** | Story Points result | XS–XXL classification (derived/presentation layer) | ✅ |
| **BCP** | CFM | Business Complexity Points via external LLM-based SDK | ❌ (by design) |

### 10. Rule Pack Engine for Externalized Policies

Organization-specific measurement rules are externalized as declarative YAML files (no scripting) in the `.specmetrics/rules/` directory. The Rule Pack Engine subscribes to `RULE_PACK_APPLIED`, loads and validates rule packs, and annotates the CFM with applied rules. Supports exclusions, complexity threshold overrides, VAF configuration, glossary overrides, and per-element annotations.

Measurement engines consume Rule Pack overrides through:
- Explicit function parameters (coefficients, thresholds)
- CFM element metadata annotations set by the Rule Pack Engine
- Environment variables (for provider selection, e.g., BCP)

### 11. Two Interaction Interfaces (CLI and MCP)

- **CLI** (Typer): commands `measure`, `plugins list`, `init`, `validate`, `export`, `publish`, `explain`
- **MCP Server**: exposes capabilities as MCP tools via JSON-RPC 2.0 over stdio or SSE

Both interfaces use the same underlying pipeline orchestration (`PipelineOrchestrator`).

### 12. Hierarchical Configuration System

Centralized configuration in `specmetrics.yml` with hierarchy: system < user < project < env vars < CLI args. Uses Pydantic Settings for validation. Supports YAML and JSON, sensitive value masking, and per-plugin configuration schemas.

### 13. Export Layer and OpenTelemetry Publisher

Measurement results can be exported to JSON, CSV, XML (built-in) or custom formats via plugins. The OpenTelemetry Publisher sends metrics via OTLP (gRPC/HTTP) with exponential backoff retry, without blocking the pipeline.

Most measurement plugins also emit direct OpenTelemetry metrics (duration histograms, item gauges, distribution histograms) via module-level OTEL instruments, following the pattern established by SFP.

### 14. Validation as an Independent Stage

The validation pipeline (F14) checks semantic consistency before measurement: missing mandatory sections, unrecognized formats, constitutional compliance. It is a separate stage that feeds into the measurement pipeline without being part of it.

### 15. Calibration Profile System (Token Points, Cognitive Points)

For engines requiring externalized calibration (weights, mappings, normalization tables), calibration profiles are loaded from `.specmetrics/calibration/<engine>.yml` YAML files via `ruamel.yaml`. Each engine provides:
- Built-in default calibration profile
- YAML loader with deep merge over defaults
- Validation on load (non-negative weights, semver versioning, profile structure)

### 16. Explainability as a First-Class Concern

Every measurement engine includes a dedicated `explainer.py` module providing:
- Per-item contribution/classification breakdown
- Ranked top-contributor identification
- Evidence reference assembly
- Distribution aggregation

The `explain` CLI command and MCP tool expose explainability data for inspection.

### 17. Graceful Degradation Pattern

All measurement engines follow the same degradation pattern:
- **Missing input** (CFM/CSM/SP result) → empty result with `MISSING_CFM`/`MISSING_CSM`/`NO_STORY_POINTS` warnings
- **Missing external dependency** (BCP SDK) → empty result with `SDK_NOT_AVAILABLE` warning
- **Missing credentials** (API keys) → empty result with `MISSING_CREDENTIALS` warning
- **Per-item failures** → item marked `status="failed"`, `total` reflects only successes
- Pipeline continues uninterrupted in all cases

## Architectural Patterns

| Pattern                     | Application                                                       |
| --------------------------- | ----------------------------------------------------------------- |
| **Pipeline**                | Sequential stage orchestration with immutable context             |
| **Plugin**                  | Discovery via entry points, central registry, interface contracts |
| **Adapter**                 | Adapters normalize specifications into the canonical model        |
| **Strategy**                | Interchangeable extraction engines and measurement engines        |
| **Factory**                 | `SemanticEngineFactory` resolves provider config to engine impl   |
| **Visitor**                 | AST visitors (HeadingVisitor, ListVisitor, etc.) traverse Markdown |
| **Event Bus**               | In-process sync event bus for inter-stage communication           |
| **Repository**              | Evidence graph and export persistence on filesystem               |
| **Value Object**            | Immutable models (CFM, CSM, PipelineEvent, all measurement results) |
| **Builder**                 | CFM/CSM construction from the evidence graph                      |
| **Chain of Responsibility** | Validation pipeline with chained rules                            |
| **Adapter (external SDK)**  | BCP wraps `bcp-calculator` SDK with retry, error translation     |

## Consequences

- Plugin-based architecture allows adding new specification frameworks and measurement engines without modifying the core
- Pipeline determinism guarantees measurement reproducibility (except BCP, which is non-deterministic by design)
- Immutability and provenance enable full audit of results
- CLI/MCP separation allows use by both humans and AI agents
- Externalized rules via Rule Packs eliminate the need to change code for organizational policies
- The evidence graph as intermediate storage enables rich queries and full traceability
- Multiple measurement engines can coexist, each producing independent results from the same canonical models
- Calibration YAML files allow organizations to tune weights, mappings, and normalization without code changes
