# Implementation Plan: Semantic Extraction

**Branch**: `005-semantic-extraction` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-semantic-extraction/spec.md`

## Summary

Implement the Semantic Extraction pipeline stage (F04) that consumes normalized Document objects from the Specification Adapter layer and produces extracted semantic elements (facts, entities, relationships, operations) with evidence provenance. Extraction is performed by pluggable providers discovered via F02, with built-in LLM-assisted extraction as the default provider.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: structlog (existing), LiteLLM (existing), Pydantic v2 (existing), F02 PluginRegistry (existing), SpecificationAdapter Protocol (F03)

**Storage**: N/A — extraction is a pipeline stage with no persistence; results are passed in-memory to the Evidence Graph layer

**Testing**: pytest

**Target Platform**: Linux

**Project Type**: library (kernel module: extraction stage + provider interface)

**Performance Goals**: 10 specification documents fully extracted within 30 seconds (SC-001); single document extraction within 5 seconds

**Constraints**: Providers are stateless; each invocation is independent; per-document error isolation (FR-004); LLM-assisted extraction must degrade gracefully without API connectivity; provider routing by document type (FR-008)

**Scale/Scope**: Single-repository extraction with multiple simultaneously installed providers; documents up to provider context limits with chunking fallback

## Constitution Check

*GATE: Phase 0 research complete. Post-design re-check passed.*

**Engaged Principles**: I (Specification First), III (Semantic Before Structural), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First: The extraction stage consumes normalized Document objects produced by the Specification Adapter layer — it operates on specifications, never on source code.
- [x] Evidence First: Every ExtractedElement includes an EvidenceReference with source document ID, section ID, and text fragment — no measurement without traceability.
- [x] Canonical Representation: Extraction produces framework-agnostic semantic elements. No downstream component depends on any SDD framework format.
- [x] Plugin-Oriented: Extraction providers are F02 plugins with type SEMANTIC. New document format support is added by installing a new provider plugin — never by modifying the core.
- [x] Layer Independence: The extraction stage consumes only the canonical Document model and produces an ExtractionResult consumed by the Evidence Graph layer. No layer depends on another's internal implementation.
- [x] Open by Default: The ExtractionProvider interface is documented in contracts. Provider routing is configuration-based and extensible.

**Research Resolution**:
- Provider interface: Protocol class (structural subtyping), matching F01 EventHandler and F03 SpecificationAdapter patterns
- LLM integration: LiteLLM gateway with configurable backends; graceful degradation when unavailable
- Evidence provenance: EvidenceReference dataclass with document_id, section_id, text fields
- Provider routing: Document type string matching against provider-declared supported types
- Error isolation: Per-document try/except within extraction stage, independent of provider choice

**Gate result**: PASS — all principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/005-semantic-extraction/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── extraction-interface.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── __init__.py
│   ├── extraction_stage.py          # NEW — ExtractionStage pipeline handler
│   ├── extraction_provider.py       # NEW — ExtractionProvider Protocol, result models
│   ├── extraction_registry.py       # NEW — provider registry wrapping F02 PluginRegistry
│   └── ... (existing F01 + F02 + F03 files)
├── plugins/
│   └── semantic/
│       └── llm_provider.py          # NEW — built-in LLM-assisted extraction provider
└── tests/
    ├── unit/
    │   ├── test_extraction_stage.py      # NEW
    │   └── test_extraction_provider.py   # NEW
    └── integration/
        └── test_extraction_pipeline.py   # NEW
```

**Structure Decision**: The extraction interface lives in `specmetrics/kernel/` because it is a core contract consumed by the Pipeline Engine. It depends on F02 (PluginRegistry) and F03 (Document model) but not on any specific provider implementation. Built-in providers live in `plugins/semantic/`.

## Complexity Tracking

No constitution violations expected. The extraction stage follows the same pattern as F03 (Specification Adapter): a Protocol class, a registry wrapping F02, and a pipeline event handler. The main complexity is the LLM-assisted provider integration, which reuses the existing LiteLLM dependency.
