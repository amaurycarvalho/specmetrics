# Implementation Plan: Measurement Engine Plugin — Story Points (Modified Fibonacci)

**Branch**: `024-measurement-engine-storypoints` | **Date**: 2026-07-17 | **Spec**: `specs/024-measurement-engine-storypoints/spec.md`

**Input**: Feature specification from `specs/024-measurement-engine-storypoints/spec.md`

## Summary

Implement a Story Points measurement engine plugin that estimates the relative implementation effort of functional work items using a Modified Fibonacci scale. The engine consumes only the Canonical Functional Model (CFM), computes a raw effort score per Functional Process via a configurable multi-factor weighted sum (business interactions, data, integrations, rules, workflow, exceptions), then normalizes to Modified Fibonacci values (1, 2, 3, 5, 8, 13, 20, 40, 100). All factor coefficients and normalization thresholds are configurable via Rule Packs.

## Technical Context

**Language/Version**: Python >=3.12 (project targets 3.13 per constitution)

**Primary Dependencies**: Pydantic v2 (models), structlog (logging)

**Storage**: In-memory measurement; Rule Pack overrides read from annotated CFM

**Testing**: pytest with pytest-benchmark for performance assertions

**Target Platform**: Linux — CLI + MCP Server (local execution)

**Project Type**: Library/CLI — Measurement Engine Plugin (follows existing SFP/FPA/SNAP patterns)

**Performance Goals**: ≤500 Functional Processes estimated in under 5 seconds (SC-003); near-linear scaling for >1000 processes (SC-007)

**Constraints**: Deterministic (identical CFM → identical Story Points), CFM-only (no CSM dependency), multi-factor weighted sum formula, Fibonacci normalization, incremental recomputation support (FR-033/FR-034)

**Scale/Scope**: 500+ Functional Processes per run; 6 default scoring factors; Modified Fibonacci scale with 9 values

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: I (Specification First), II (Specification as a Measurable Asset), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization), X (AI-Friendly by Design), XI (Observability), XII (Open by Default)

**Compliance Verifications**:
- [x] Specification First (I): Consumes only the Canonical Functional Model — the authoritative representation of functional requirements.
- [x] Specification as a Measurable Asset (II): Produces deterministic Story Points as a reusable planning and benchmarking metric.
- [x] LLM-Assisted, Deterministic Results (IV): FR-002 explicitly prohibits LLM participation. All calculation is purely deterministic.
- [x] Evidence First (V): Every estimated work item preserves evidence references to originating CFM elements (FR-004, FR-027).
- [x] Canonical Representation (VII): Only the framework-independent CFM is consumed. No OpenSpec/SpecKit-specific dependencies.
- [x] Plugin-Oriented (VIII): Implemented as a Measurement Engine plugin discoverable via Entry Points (FR-007, SC-005).
- [x] Rule Externalization (IX): Factor coefficients, normalization thresholds, and estimation heuristics are externalized through Rule Packs (FR-005, FR-023–FR-026).
- [x] AI-Friendly by Design (X): Output is machine-readable JSON (FR-006), consumable by AI agents for portfolio analysis.
- [x] Observability (XI): Emits structured logs (FR-035) and OpenTelemetry metrics (FR-036) including duration histogram, work item gauge, and distribution histogram.
- [x] Open by Default (XII): Plugin interface, output format, and Rule Pack schema are documented.

## Project Structure

### Documentation (this feature)

```text
specs/024-measurement-engine-storypoints/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
specmetrics/plugins/measurement/storypoints/    # New measurement plugin
├── __init__.py
├── plugin.py                       # StoryPointsPlugin, StoryPointsHandler, create_metadata()
├── models.py                       # StoryPointMeasurementResult, FunctionalWorkItem,
#                                   # RawEffortScore, StoryPointEstimate, MeasurementEvidence
├── calculator.py                   # Multi-factor weighted sum: for each Functional Process,
#                                   # score each factor, apply coefficient, sum, normalize
├── factor_scorer.py                # Default factor scoring from CFM element characteristics
├── normalizer.py                   # Modified Fibonacci normalization (1,2,3,5,8,13,20,40,100)
└── explainer.py                    # Explainability breakdown per FR-027

tests/
├── unit/
│   ├── test_storypoints_calculator.py       # Core multi-factor calculation
│   ├── test_storypoints_factor_scorer.py     # Factor scoring from CFM
│   ├── test_storypoints_normalizer.py        # Fibonacci normalization
│   └── test_storypoints_models.py            # Model construction, serialization
├── contract/
│   └── test_storypoints_measurement.py       # Measurement API contract
└── integration/
    └── test_storypoints_pipeline.py          # Full pipeline integration
```

**Structure Decision**: Follows existing measurement plugin convention. Dedicated `factor_scorer.py` for the multi-factor scoring algorithm and `normalizer.py` for Fibonacci normalization.

## Complexity Tracking

*No constitution violations to justify.*
