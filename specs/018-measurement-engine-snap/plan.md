# Implementation Plan: Measurement Engine Plugin — SNAP

**Branch**: `018-measurement-engine-snap` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/018-measurement-engine-snap/spec.md`

## Summary

Implement a deterministic SNAP (Software Non-functional Assessment Process) measurement engine as a discoverable SpecMetrics plugin. The engine consumes the Canonical Functional Model (CFM) enriched with semantic metadata, identifies assessment candidates via metadata markers, organizes them into independently measurable categories, applies organizational Rule Packs, and produces traceable, explainable SNAP assessments with fixed contribution values per category. Every assessed item preserves evidence references to its originating CFM elements.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**:
- `pydantic` v2 — for CFM model consumption and SNAP assessment result models (platform standard)
- Python entry points — for plugin discovery via `specmetrics.plugins.measurement`
- `structlog` — for structured logging (platform standard)
- `opentelemetry-api` — for assessment duration histogram and per-category count gauges (platform standard)

**Storage**: N/A (in-memory assessment; results propagated via pipeline events)

**Testing**: pytest (platform standard)

**Target Platform**: Linux desktop/server (local execution, CLI + MCP)

**Project Type**: Library/Plugin within the SpecMetrics platform (`specmetrics/plugins/measurement/`)

**Performance Goals**: Complete SNAP assessment for medium-sized CFMs (≤500 assessment candidates) within 5 seconds (SC-003); handle large assessments with ≤15% deviation per doubling (SC-007)

**Constraints**:
- Deterministic execution — identical CFM + identical Rule Packs → byte-identical results
- No LLM inference or non-deterministic operations (FR-002)
- Must not modify the input CFM (immutable pipeline invariant)
- Assessment organized into independent categories with SemVer versioning (FR-015)
- Each assessed item belongs to exactly one category (FR-012)
- No complexity classification
- Fixed contribution values per category — specific values sourced from licensed IFPUG SNAP specification
- Every assessed item must preserve category-specific evidence (FR-022, FR-030)

**Scale/Scope**: Single assessment methodology (SNAP only); complements FPA and SFP

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: IV (LLM-Assisted, Deterministic Results), VI (Explainability by Design), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization)

**Compliance Verifications**:
- [x] Specification First: The engine consumes the CFM, which is derived from specifications. It never reads raw spec documents — compliant via Canonical Isolation.
- [x] Evidence First: FR-030 requires every assessed item to expose originating CFM element, category, Rule Pack, contribution, and evidence references. Each item is traceable.
- [x] Canonical Representation: FR-001 restricts the engine to consume only the CFM and its associated semantic metadata. No framework-specific artifacts leak into assessment logic.
- [x] Plugin-Oriented: FR-007 requires implementation as a discoverable plugin. The engine registers via Python Entry Points and communicates through Kernel contracts.
- [x] Rule Externalization: FR-005 and FR-025–FR-029 require Rule Packs as external inputs. Assessment policies are never hardcoded; defaults apply only when no Rule Pack is provided.
- [x] Layer Independence: The engine depends only on the CFM model (from F06) and the plugin contract (from F02). It has no knowledge of adapters, extraction, or graph internals.
- [x] Open by Default: Plugin interface and Rule Pack format are documented contracts. Assessment output format is standardized for downstream export/pub plugins.

## Project Structure

### Documentation (this feature)

```text
specs/018-measurement-engine-snap/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # SNAP methodology research and design decisions
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Validation guide
├── contracts/
│   └── measurement-plugin-interface.md
└── checklists/
    └── requirements.md  # Quality checklist
```

### Source Code (repository root)

```text
specmetrics/
└── plugins/
    └── measurement/
        └── snap/
            ├── __init__.py
            ├── plugin.py          # Plugin entry point (discovery + registration)
            ├── assessor.py        # Assessment candidate identification and categorization
            ├── models.py          # Pydantic models for assessment results
            ├── rule_applicator.py # Rule Pack processing
            └── explainer.py       # Evidence trail + explanation builder

tests/
├── unit/
│   └── measurement/
│       └── snap/
│           ├── test_assessor.py
│           ├── test_rule_applicator.py
│           └── test_plugin.py
└── integration/
    └── measurement/
        └── snap/
            └── test_full_assessment.py
```

**Structure Decision**: Single plugin under `specmetrics/plugins/measurement/snap/`, following the existing FPA/SFP plugin pattern. SNAP shares the same project infrastructure but uses category-based assessment with semantic metadata-driven candidate identification.

## Complexity Tracking

No constitution violations detected. All engaged principles are satisfied by the design decisions documented above.
