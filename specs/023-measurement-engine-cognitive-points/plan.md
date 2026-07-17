# Implementation Plan: Measurement Engine Plugin — Cognitive Points

**Branch**: `023-measurement-engine-cognitive-points` | **Date**: 2026-07-17 | **Spec**: `specs/023-measurement-engine-cognitive-points/spec.md`

**Input**: Feature specification from `specs/023-measurement-engine-cognitive-points/spec.md`

## Summary

Implement a Cognitive Points measurement engine plugin that estimates the human cognitive effort required for specification review and delivery validation in AI-assisted software engineering. The engine consumes both CFM and CSM, classifies each canonical element into a Bloom cognitive level, applies configurable weights, sums contributions into Specification Review Effort and Functional Validation Effort, and normalizes the total via a Fibonacci lookup table. All calibration parameters (Bloom mappings, weights, normalization table) are externalized via YAML.

## Technical Context

**Language/Version**: Python >=3.12 (project targets 3.13 per constitution)

**Primary Dependencies**: Pydantic v2 (models), ruamel.yaml (calibration profile loading), structlog (logging)

**Storage**: In-memory measurement; calibration profiles loaded from YAML files

**Testing**: pytest with pytest-benchmark for performance assertions

**Target Platform**: Linux — CLI + MCP Server (local execution)

**Project Type**: Library/CLI — Measurement Engine Plugin (follows existing SFP/FPA/SNAP/Token Points patterns)

**Performance Goals**: 500 canonical elements (CFM + CSM combined) measured in under 2 seconds (SC-006)

**Constraints**: Deterministic (identical CFM + CSM → identical Cognitive Points), all calibration via YAML without code changes, every contribution traceable to Bloom level and evidence, Fibonacci normalization externally configurable

**Scale/Scope**: 500+ canonical elements per run; two effort components; 6 Bloom taxonomy levels

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: I (Specification First), II (Specification as a Measurable Asset), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization), X (AI-Friendly by Design), XI (Observability), XII (Open by Default), XIII (Evolution Without Disruption)

**Compliance Verifications**:
- [x] Specification First (I): Consumes only CFM and CSM — never raw framework-specific documents.
- [x] Specification as a Measurable Asset (II): Produces structured Cognitive Points as a reusable capacity planning metric.
- [x] LLM-Assisted, Deterministic Results (IV): LLMs MAY assist semantic extraction; Cognitive Points calculation is purely deterministic.
- [x] Evidence First (V): Every CognitiveContribution preserves evidence reference to its originating canonical element.
- [x] Canonical Representation (VII): Consumes only framework-independent models (CFM, CSM).
- [x] Plugin-Oriented (VIII): Implemented as Measurement Engine plugin subscribing to `MEASUREMENT_COMPLETED`. Registered via entry point.
- [x] Rule Externalization (IX): All Bloom mappings, cognitive weights, normalization tables externalized via YAML calibration profiles.
- [x] AI-Friendly by Design (X): Structured JSON output consumable by AI agents for capacity planning automation.
- [x] Observability (XI): Emits `CognitivePointsMeasured` event. Metadata captures element counts, Bloom distribution, duration.
- [x] Open by Default (XII): Result schema is documented Pydantic model. Calibration format is documented YAML.
- [x] Evolution Without Disruption (XIII): Adding new element types or Bloom levels does not change the three-stage formula. Calibration profiles versioned.

## Project Structure

### Documentation (this feature)

```text
specs/023-measurement-engine-cognitive-points/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
specmetrics/plugins/measurement/cognitive_points/   # New measurement plugin
├── __init__.py
├── plugin.py                      # CognitivePointsPlugin, CognitivePointsHandler, create_metadata()
├── models.py                      # CognitivePointsMeasurement, SpecificationReviewEffort,
#                                  # FunctionalValidationEffort, CognitiveContribution
├── calculator.py                  # Three-stage calculation: (1) Bloom-weighted sum per component,
#                                  # (2) total raw, (3) Fibonacci normalize
├── bloom_classifier.py            # Element-to-Bloom-level mapping (default + overridable)
├── fibonacci_normalizer.py        # Raw score → Fibonacci normalization with configurable thresholds
├── calibration.py                 # CognitiveCalibrationProfile model, defaults, YAML loader
└── explainer.py                   # Explainability breakdown builder

tests/
├── unit/
│   ├── test_cognitive_points_calculator.py   # Core three-stage calculation
│   ├── test_cognitive_points_bloom.py         # Bloom classification
│   ├── test_cognitive_points_normalizer.py    # Fibonacci normalization
│   ├── test_cognitive_points_calibration.py   # Calibration loading
│   └── test_cognitive_points_models.py        # Model construction, serialization
├── contract/
│   └── test_cognitive_points_measurement.py   # Measurement API contract
└── integration/
    └── test_cognitive_points_pipeline.py      # Full pipeline integration
```

**Structure Decision**: Follows existing measurement plugin convention. Pattern matches Token Points (022) but adds dedicated `bloom_classifier.py` and `fibonacci_normalizer.py` modules for the two unique algorithmic components.

## Complexity Tracking

*No constitution violations to justify.*
