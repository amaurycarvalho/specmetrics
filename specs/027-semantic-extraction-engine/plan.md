# Implementation Plan: Semantic Extraction Engine

**Branch**: `027-semantic-extraction-engine` | **Date**: 2026-07-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/027-semantic-extraction-engine/spec.md`

## Summary

Implement the Semantic Extraction Engine — a unified abstraction layer that decouples the measurement pipeline from any specific semantic extraction strategy. The engine provides two implementations behind a single `SemanticExtractionEngine` interface: `DeterministicSemanticEngine` (offline structural analysis via Markdown AST) and `LiteLLMSemanticEngine` (LLM-assisted extraction via existing LiteLLM gateway). A `SemanticEngineFactory` resolves the configured LLM provider to the correct engine during pipeline initialization. Both engines produce identical `ExtractionResult` models with full evidence provenance.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: structlog (existing), Pydantic v2 (existing), markdown-it-py (existing constitution tech stack), LiteLLM (existing), ExtractionProvider/ProviderRouter (005 existing), NetworkX (existing)

**Storage**: N/A — extraction is a pipeline stage with no persistence; results passed in-memory to Evidence Graph layer

**Testing**: pytest

**Target Platform**: Linux

**Project Type**: library (kernel module — engine interface, factory, and two implementations)

**Performance Goals**: 10 specification documents fully extracted within 5 seconds for deterministic engine (SC-001); no specific LLM-assisted latency target (depends on provider)

**Constraints**: Deterministic engine must operate fully offline with zero external dependencies (FR-006); LLM engine must fail cleanly on provider unavailability with no silent fallback to deterministic (FR-012, Q1); both engines must produce byte-identical output for identical inputs (NFR-001); engine selection occurs once during pipeline init (NFR-002)

**Scale/Scope**: Single-repository extraction; deterministic engine limited to document size that fits in memory for AST parsing; LiteLLM engine subject to provider context limits

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: I (Specification First), III (Semantic Before Structural), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First: The engine consumes normalized Document objects produced by the Specification Adapter layer — it operates on specifications, never on source code.
- [x] Evidence First: Every ExtractedElement includes an EvidenceReference with document_id, section_id, and text — no measurement without traceability (FR-010).
- [x] Canonical Representation: Both DeterministicSemanticEngine and LiteLLMSemanticEngine produce identical ExtractionResult models. Downstream stages consume only this canonical model (FR-009).
- [x] Plugin-Oriented: Additional engine implementations can be added by extending SemanticEngineFactory and implementing the SemanticExtractionEngine Protocol — no core pipeline changes required.
- [x] Rule Externalization: Extraction rules are external YAML rule packs loaded at engine init (Rule Pack format defined in research.md). Users add rules without modifying engine code (FR-008).
- [x] Layer Independence: The pipeline invokes only the SemanticExtractionEngine interface (FR-005). SemanticEngineFactory resolves implementation once at init. No layer depends on another's internals.
- [x] Open by Default: The engine interface is documented in contracts/engine-interface.md. CLI and MCP expose only LLM provider configuration — engine selection is internal (FR-013).

**Research Resolution**:
- Engine interface: Protocol class (structural subtyping) matching ExtractionProvider and other kernel Protocol patterns
- Factory pattern: Resolve provider string → engine implementation; returns SemanticExtractionEngine Protocol
- Deterministic engine architecture: Markdown AST visitor pattern + rule engine + pattern library (per RFC-031)
- Rule pack format: External YAML definitions with name, pattern, priority, and confidence fields
- LiteLLM engine: Wraps exiting LiteLLM gateway; delegates to configured provider via model string
- Content-hash ID: `sha256(document_id + "::" + section_path + "::" + text)[:16]`
- LLM failure behavior: Fail cleanly — no silent fallback to deterministic (Q1)
- Rule conflict resolution: Explicit priority scores (1–100); higher wins on conflict (Q3)
- Confidence model: Deterministic engine uses RFC-031 table; LiteLLM engine uses logprobs (Q4)
- Statistics: Standard set — documents processed, elements extracted, elements by type, duration, errors (Q5)

**Gate result**: PASS — all principles satisfied. No unjustified complexity introduced.

## Project Structure

### Documentation (this feature)

```text
specs/027-semantic-extraction-engine/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── engine-interface.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── __init__.py
│   ├── semantic_extraction_engine.py    # NEW — SemanticExtractionEngine Protocol + factory
│   ├── deterministic_engine.py          # NEW — DeterministicSemanticEngine implementation
│   ├── litellm_engine.py                # NEW — LiteLLMSemanticEngine implementation
│   ├── engine_rule.py                   # NEW — Rule definition model + rule pack loader
│   ├── engine_visitors.py               # NEW — AST visitors (HeadingVisitor, ListVisitor, etc.)
│   ├── engine_patterns.py               # NEW — Pattern library (GWT, User Story, etc.)
│   └── ... (existing extraction_provider.py, extraction_stage.py, etc.)
├── plugins/
│   └── semantic/
│       ├── llm_provider.py              # EXISTING — may be refactored to use LiteLLMSemanticEngine
│       ├── openspec_provider.py         # EXISTING
│       └── speckit_provider.py          # EXISTING
└── tests/
    ├── unit/
    │   ├── test_semantic_extraction_engine.py   # NEW
    │   ├── test_deterministic_engine.py         # NEW
    │   ├── test_litellm_engine.py               # NEW
    │   ├── test_engine_rule.py                  # NEW
    │   └── test_engine_visitors.py              # NEW
    └── integration/
        └── test_engine_pipeline.py              # NEW
```

**Structure Decision**: The engine interface and implementations live in `specmetrics/kernel/` because they are core pipeline abstractions — the Pipeline Engine depends on `SemanticExtractionEngine`, not on any specific provider. The factory is co-located in the kernel as it wires configuration to implementation. Rule definitions (external YAML packs) are loaded at engine init, supporting Rule Externalization (Principle IX). Existing extraction providers in `plugins/semantic/` continue to work; the `LiteLLMSemanticEngine` wraps the LiteLLM gateway used by those providers.

## Design Principles

The engine design follows these principles (per RFC-030):

| Principle | How Applied |
|-----------|-------------|
| **Strategy Pattern** | `SemanticExtractionEngine` is the strategy interface; `DeterministicSemanticEngine` and `LiteLLMSemanticEngine` are concrete strategies selected by the factory at runtime. |
| **Dependency Inversion** | The pipeline depends on the `SemanticExtractionEngine` abstraction, not on concrete implementations. The factory inverts control of engine selection. |
| **Open/Closed Principle** | New engine implementations can be added without modifying existing code — the factory mapping is extended, the pipeline is unchanged. |
| **Layer Independence** | The engine interface is the sole contract between the Pipeline layer and the extraction layer. No layer depends on another's internals. |
| **Deterministic Interfaces** | The engine interface and `ExtractionResult` output model are fully deterministic. LLM-assisted extraction enriches content but conforms to the same deterministic contract. |

## Complexity Tracking

No constitution violations expected. The engine follows the existing kernel Protocol pattern (matching `ExtractionProvider`, `EventHandler`, `SpecificationAdapter`). The deterministic engine's visitor + rule engine architecture is the primary complexity, but it is isolated behind the `SemanticExtractionEngine` interface. The LiteLLM engine reuses the existing LiteLLM dependency and provider routing.
