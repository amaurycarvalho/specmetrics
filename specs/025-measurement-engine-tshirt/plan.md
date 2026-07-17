# Implementation Plan: Measurement Engine Plugin — T-Shirt Sizing

**Branch**: `025-measurement-engine-tshirt` | **Date**: 2026-07-17 | **Spec**: `specs/025-measurement-engine-tshirt/spec.md`

**Input**: Feature specification from `specs/025-measurement-engine-tshirt/spec.md`

## Summary

Implement a T-Shirt Sizing measurement engine plugin that classifies functional work items into relative effort categories (XS, S, M, L, XL, XXL) by applying a configurable lookup table against deterministic Story Point estimates. The plugin does not perform independent estimation — it derives T-Shirt Sizes from Story Points results accessed via a dedicated `TSHIRT_CLASSIFICATION_COMPLETED` pipeline event sequenced after `MEASUREMENT_COMPLETED`. Returns empty result with warnings when Story Points are unavailable.

## Technical Context

**Language/Version**: Python >=3.12 (project targets 3.13 per constitution)

**Primary Dependencies**: Pydantic v2 (models), structlog (logging)

**Storage**: In-memory classification; mapping table from built-in defaults or Rule Pack overrides

**Testing**: pytest

**Target Platform**: Linux — CLI + MCP Server (local execution)

**Project Type**: Library/CLI — Measurement Engine Plugin (derived/presentation layer over Story Points)

**Performance Goals**: ≤500 Functional Processes classified in under 1 second (SC-003); near-linear scaling for >1000 (SC-007)

**Constraints**: Deterministic (identical SP → identical T-Shirt sizes), no independent estimation (FR-013), configurable mapping via Rule Packs, reads SP results from `ctx.measurement_result` via dedicated pipeline event

**Scale/Scope**: 500+ Functional Processes per run; 6 default size categories; lookup-table-based classification (O(1) per item)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization), X (AI-Friendly by Design), XI (Observability), XII (Open by Default)

**Compliance Verifications**:
- [x] LLM-Assisted, Deterministic Results (IV): No LLM participation (FR-002). Classification is purely deterministic lookup.
- [x] Evidence First (V): Every classified item preserves evidence reference to SP result and CFM (FR-004, FR-025).
- [x] Canonical Representation (VII): Consumes deterministic measurement artifacts generated from the CFM — never framework-specific artifacts.
- [x] Plugin-Oriented (VIII): Implemented as a Measurement Engine plugin discovered via Entry Points (FR-007, SC-005).
- [x] Rule Externalization (IX): Size scale, mapping ranges, and classification policies externalized via Rule Packs (FR-005, FR-021–FR-024).
- [x] AI-Friendly by Design (X): Output is machine-readable JSON (FR-006) consumable by AI agents for portfolio analysis.
- [x] Observability (XI): Emits structured logs (FR-033) and OpenTelemetry metrics (FR-034) including duration histogram, item gauge, and distribution histogram.
- [x] Open by Default (XII): Plugin interface, output format, and mapping table schema are documented.

## Project Structure

### Documentation (this feature)

```text
specs/025-measurement-engine-tshirt/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
specmetrics/plugins/measurement/tshirt/         # New measurement plugin
├── __init__.py
├── plugin.py                       # TShirtPlugin, TShirtHandler, create_metadata()
├── models.py                       # TShirtMeasurementResult, FunctionalWorkItem, TShirtSize,
#                                   # MeasurementEvidence
├── classifier.py                   # SP-to-TShirt lookup with configurable mapping table
└── explainer.py                    # Explainability per FR-025

specmetrics/kernel/events.py                     # MODIFIED: add TSHIRT_CLASSIFICATION_COMPLETED
specmetrics/kernel/pipeline_engine.py            # MODIFIED: add to CANONICAL_EVENT_ORDER

tests/
├── unit/
│   ├── test_tshirt_classifier.py       # Mapping lookup, custom scales, invalid config
│   └── test_tshirt_models.py           # Model construction, serialization
├── contract/
│   └── test_tshirt_measurement.py      # Measurement API contract
└── integration/
    └── test_tshirt_pipeline.py         # Full pipeline: SP → T-Shirt
```

**Structure Decision**: Minimal plugin — only 4 source files (excluding `__init__.py`). The classifier is a simple lookup table with no multi-factor scoring or normalization needed.

## Complexity Tracking

*No constitution violations to justify.*
