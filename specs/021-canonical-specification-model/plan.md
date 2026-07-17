# Implementation Plan: Canonical Specification Model Builder

**Branch**: `021-canonical-specification-model` | **Date**: 2026-07-17 | **Spec**: `specs/021-canonical-specification-model/spec.md`

**Input**: Feature specification from `specs/021-canonical-specification-model/spec.md`

## Summary

Build a new pipeline stage that transforms an EvidenceGraph into a framework-independent CanonicalSpecificationModel (CSM). The CSM captures specification-process semantics (Decisions, Assumptions, Constraints, Risks, Open Questions, Acceptance Criteria, Glossary Terms, Specification Activities) and is consumed by downstream measurement engines (Token Points, Cognitive Points) without exposing SDD framework terminology. All elements inherit from a CsmElement base with UUID v4 identity, evidence provenance, and lifecycle status.

## Technical Context

**Language/Version**: Python >=3.12 (project targets 3.13 per constitution)

**Primary Dependencies**: Pydantic v2 (models), NetworkX (graph traversal if needed), structlog (logging), ruamel.yaml (classification rules config)

**Storage**: In-memory model with JSON serialization (via `model_dump_json`) for inspection and debugging

**Testing**: pytest with pytest-benchmark for performance assertions

**Target Platform**: Linux — CLI + MCP Server (local execution; no centralized server for v0.1)

**Project Type**: Library/CLI package — extends the existing stage plugin architecture

**Performance Goals**: 500 specification-related elements transformed in under 3 seconds (SC-001)

**Constraints**: Immutable model (`model_config = {"frozen": True}`), byte-equivalent for identical inputs (SC-006), deterministic classification (FR-013)

**Scale/Scope**: Evidence graphs of 500+ extracted elements per run; 9 canonical categories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: I (Specification First), II (Specification as a Measurable Asset), V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), X (AI-Friendly by Design), XI (Observability as a Native Capability), XII (Open by Default), XIII (Evolution Without Disruption), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First (I): CSM consumes specification artifacts extracted from EvidenceGraph, not source code or implementation artifacts.
- [x] Evidence First (V): Every CsmElement preserves `evidence_references` with full provenance (document, section, fragment). BuildMetadata tracks unclassified elements and conflicts.
- [x] Canonical Representation (VII): Core purpose — removes all framework-specific terminology, normalizes into canonical SpecificationActivity, Decision, Assumption, etc.
- [x] Layer Independence (XIV): CSM exposes a documented category-based query interface (`get_elements(category)`, `get_by_evidence(ref)`). Downstream engines never import framework-specific modules.
- [x] Specification as a Measurable Asset (II): CSM bears measurable metadata (category counts, build duration) that Token Points and Cognitive Points consume for estimation.
- [x] Plugin-Oriented (VIII): CSM Builder is a stage plugin subscribing to `EVIDENCE_GRAPH_BUILT`. Classification rules could be externalized as Rule Packs in future iterations.
- [x] AI-Friendly by Design (X): CSM query interface supports programmatic access; serialization to JSON enables AI agent consumption via MCP.
- [x] Observability as a Native Capability (XI): Builder emits `CanonicalSpecificationModelBuilt` event; BuildMetadata captures counts, duration, conflicts, unclassified.
- [x] Open by Default (XII): CSM interface is documented via Python Protocol; serialization uses standard JSON.
- [x] Evolution Without Disruption (XIII): Adding new canonical categories does not require changes to the query interface contract. Backward compatibility maintained via the base CsmElement pattern.
- [ ] Rule Externalization (IX): Deferred — classification rules are hardcoded in the classifier for v0.1. Future iterations should externalize as Rule Packs.

## Project Structure

### Documentation (this feature)

```text
specs/021-canonical-specification-model/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
specmetrics/kernel/csm/           # CSM kernel module (new)
├── __init__.py
├── model.py                      # CsmElement base, all entity models
├── metadata.py                   # BuildMetadata, ClassificationConflict
├── classifier.py                 # Deterministic classification rules
├── builder.py                    # build() function + CsmBuilderStage handler
├── activity_classifier.py        # SpecificationActivity type detection
└── evidence_processing.py        # Evidence graph traversal helpers

specmetrics/plugins/stage/
└── csm_builder.py                # Stage plugin metadata (new)

tests/
├── unit/
│   ├── test_csm_model.py         # Entity construction, immutability, serialization
│   ├── test_csm_builder.py       # build() with sample evidence graphs
│   ├── test_csm_classifier.py    # Classification rules for each canonical category
│   └── test_csm_metadata.py      # BuildMetadata correctness
├── contract/
│   └── test_csm_interface.py     # Downstream consumer protocol conformance
└── integration/
    └── test_csm_pipeline_stage.py # Full pipeline integration: EG → CSM
```

**Structure Decision**: Single project (existing monorepo). CSM follows the same `kernel/{module}/` layout as CFM (`kernel/cfm/`). Stage plugin registration parallels `cfm_builder.py`. Tests mirror existing test structure.

## Complexity Tracking

*No constitution violations to justify.*
