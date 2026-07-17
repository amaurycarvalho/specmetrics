# Implementation Plan: Deterministic Semantic Engine

**Branch**: `028-deterministic-semantic-engine` | **Date**: 2026-07-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/028-deterministic-semantic-engine/spec.md`

## Summary

Implement the DeterministicSemanticEngine — the offline-capable implementation of the SemanticExtractionEngine interface (F27). The engine parses specification documents into a Markdown AST, traverses it with dedicated visitors (HeadingVisitor, ListVisitor, TableVisitor, etc.), applies a rule engine with external YAML rule packs, and produces ExtractionResult with evidence references, confidence scores, and processing statistics. Zero external dependencies. Byte-identical output for identical inputs.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: structlog (existing), Pydantic v2 (existing), markdown-it-py (existing constitution tech stack), ruamel.yaml (existing), SemanticExtractionEngine Protocol (F27 existing)

**Storage**: N/A — extraction is a pipeline stage with no persistence; results passed in-memory to Evidence Graph layer

**Testing**: pytest

**Target Platform**: Linux

**Project Type**: library (kernel module — deterministic engine implementation + visitor classes + rule engine + pattern library)

**Performance Goals**: 10 specification documents fully extracted within 5 seconds (SC-001); linear time relative to document size (FR-012)

**Constraints**: Zero external dependencies (FR-002); no regex-based parsing as primary mechanism (FR-003); evidence references mandatory on every element (FR-008); deterministic confidence scores per RFC-031 table (FR-009); byte-identical output for identical inputs (FR-011)

**Scale/Scope**: Single-repository extraction; limited to document size fitting in memory for AST parsing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: I (Specification First), III (Semantic Before Structural), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), IX (Rule Externalization), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First: The engine consumes normalized Document objects from the Specification Adapter layer — it operates on specifications, never on source code.
- [x] Evidence First: Every ExtractedElement includes an EvidenceReference with document_id, section_id, text, and extraction rule identifier (FR-008). Evidence is mandatory.
- [x] Canonical Representation: The engine produces ExtractionResult conforming to the F27 canonical model (same fields, same content-hash ID scheme). No downstream component depends on deterministic-specific artifacts.
- [x] Rule Externalization: Extraction rules are organized as external YAML rule packs loaded at engine init (research.md section 3–4). Users add custom rules without modifying engine code (FR-013).
- [x] Layer Independence: The engine implements the SemanticExtractionEngine interface (F27). The pipeline invokes only this interface. No layer knows the engine implementation.
- [x] Open by Default: Internal engine contracts are documented in contracts/deterministic-engine-interface.md and contracts/rule-pack-schema.md.

**Research Resolution**:
- Markdown AST parsing: markdown-it-py flat token stream with nesting indicators
- Visitor pattern: One visitor class per AST token type (HeadingVisitor, ListVisitor, etc.)
- Rule engine: Two-phase — visitors produce observations, rules match observations to elements
- Rule pack format: External YAML with id, name, pattern, type, confidence, priority fields
- Evidence model: F27 canonical EvidenceReference + extraction rule identifier field
- Content-hash ID: sha256(doc_id + "::" + section + "::" + text)[:16]
- Conflict resolution: Numeric priority scores (1–100); higher wins; ties by rule ID lexicographic
- Confidence table: Explicit heading=1.00, framework convention=0.95, structural heuristic=0.85, pattern inference=0.70
- Statistics: Standard set — documents processed, elements extracted, elements by type, duration, errors

**Gate result**: PASS — all principles satisfied. No unjustified complexity introduced.

## Project Structure

### Documentation (this feature)

```text
specs/028-deterministic-semantic-engine/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── deterministic-engine-interface.md
│   └── rule-pack-schema.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── __init__.py
│   ├── semantic_extraction_engine.py    # EXISTING (F27) — Protocol + factory
│   ├── deterministic_engine.py          # NEW — DeterministicSemanticEngine
│   ├── engine_rule.py                   # NEW — ExtractionRule model + RulePackLoader
│   ├── engine_visitors.py               # NEW — AST visitors (HeadingVisitor, ListVisitor, etc.)
│   ├── engine_patterns.py               # NEW — PatternLibrary (loads rule packs, matches)
│   ├── rules/                           # NEW directory
│   │   └── default_rule_pack.yaml       # NEW — Built-in rules (User Story, GWT, etc.)
│   └── ... (existing extraction_provider.py, extraction_stage.py, etc.)
└── tests/
    ├── unit/
    │   ├── test_deterministic_engine.py    # NEW
    │   ├── test_engine_rule.py             # NEW
    │   ├── test_engine_visitors.py         # NEW
    │   └── test_engine_patterns.py         # NEW
    └── integration/
        └── test_deterministic_pipeline.py  # NEW
```

**Structure Decision**: The deterministic engine lives in `specmetrics/kernel/` as a concrete implementation of the F27 `SemanticExtractionEngine` Protocol. Internal components (visitors, rule engine, pattern library) are separated into their own modules for testability and single responsibility. Built-in rule packs are stored in a `rules/` subdirectory under kernel. The engine reuses the existing `markdown-it-py` parser already in the tech stack.

## Design Principles

| Principle | How Applied |
|-----------|-------------|
| **Single Responsibility** | Each AST visitor class handles exactly one token type; the rule engine is separate from visitors |
| **Open/Closed Principle** | New rule packs can be added as YAML files without modifying any Python code (FR-013) |
| **Deterministic Interfaces** | The engine and all internal components produce deterministic output; no randomness or external state |
| **Separation of Concerns** | Parsing (visitors) is separated from semantic interpretation (rule engine) |
| **Evidence First** | Every ExtractedElement includes an EvidenceReference with the extraction rule ID that produced it |

## Complexity Tracking

No constitution violations expected. The visitor + rule engine architecture follows established patterns in the project (F05 ExtractionProvider uses Protocol, F03 SpecificationAdapter uses visitors). The main complexity is the rule matching engine, but it is isolated in `engine_rule.py` and `engine_patterns.py`.
