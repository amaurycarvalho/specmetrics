# Implementation Plan: Measurement Engine Plugin — Token Points

**Branch**: `022-measurement-engine-token-points` | **Date**: 2026-07-17 | **Spec**: `specs/022-measurement-engine-token-points/spec.md`

**Input**: Feature specification from `specs/022-measurement-engine-token-points/spec.md`

## Summary

Implement a Token Points measurement engine plugin that estimates the computational cost of AI-assisted software engineering from specification models. The engine consumes both the Canonical Functional Model (CFM) and the Canonical Specification Model (CSM), calculates Specification Cost and Code Generation Cost as separate components, and produces a fully traceable, deterministic measurement with per-element explainability. Calibration weights are externalized via hierarchical YAML profiles.

## Technical Context

**Language/Version**: Python >=3.12 (project targets 3.13 per constitution)

**Primary Dependencies**: Pydantic v2 (models), ruamel.yaml (calibration profile loading), structlog (logging)

**Storage**: In-memory measurement; calibration profiles loaded from YAML files in `.specmetrics/calibration/`

**Testing**: pytest with pytest-benchmark for performance assertions

**Target Platform**: Linux — CLI + MCP Server (local execution)

**Project Type**: Library/CLI — Measurement Engine Plugin (follows existing SFP/FPA/SNAP plugin pattern)

**Performance Goals**: 500 canonical elements (CFM + CSM combined) measured in under 2 seconds (SC-006)

**Constraints**: Deterministic (identical CFM + CSM → identical Token Points), calibration via YAML without code changes, all contributions traceable

**Scale/Scope**: 500+ canonical elements per run; two cost components with ~15 entity types across both models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: I (Specification First), II (Specification as a Measurable Asset), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization), X (AI-Friendly by Design), XI (Observability), XII (Open by Default), XIII (Evolution Without Disruption)

**Compliance Verifications**:
- [x] Specification First (I): Token Points consume only canonical models (CFM for code cost, CSM for spec cost) — never raw framework-specific documents.
- [x] Specification as a Measurable Asset (II): Produces structured Token Points measurement as a reusable, auditable engineering metric for planning and budgeting.
- [x] LLM-Assisted, Deterministic Results (IV): LLMs MAY assist extraction, but Token Points calculation is purely deterministic — same CFM + CSM + calibration → same result.
- [x] Evidence First (V): Every TokenContribution preserves evidence reference to its originating canonical element. Full provenance chain maintained.
- [x] Canonical Representation (VII): Consumes CFM and CSM — both are framework-independent canonical models. No OpenSpec/SpecKit-specific dependencies.
- [x] Plugin-Oriented (VIII): Implemented as a Measurement Engine plugin subscribing to `MEASUREMENT_COMPLETED`. Registered via entry point in `pyproject.toml` alongside SFP, FPA, SNAP.
- [x] Rule Externalization (IX): All weighting factors are externalized in YAML CalibrationProfile files. Built-in defaults provided. Organization overrides replace without code changes (FR-012 through FR-015).
- [x] AI-Friendly by Design (X): Token Points measurement is a structured, machine-readable artifact consumed via CLI and MCP. JSON serialization enables AI agent integration.
- [x] Observability (XI): Engine emits `TokenPointsMeasured` pipeline event. Measurement duration, element counts, and contribution breakdown captured for telemetry.
- [x] Open by Default (XII): Measurement result schema is a documented Pydantic model. Calibration profile format is documented YAML. No proprietary formats.
- [x] Evolution Without Disruption (XIII): Adding new weighted entity types does not change the calculation formula (always simple sum). Calibration profiles versioned for backward compatibility.

## Project Structure

### Documentation (this feature)

```text
specs/022-measurement-engine-token-points/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
specmetrics/plugins/measurement/token_points/   # New measurement plugin
├── __init__.py
├── plugin.py                      # Plugin class, TokenPointsHandler, create_metadata()
├── models.py                      # TokenPointsMeasurement, SpecificationCost, CodeGenerationCost, TokenContribution
├── calculator.py                  # Core calculation logic (sum of weighted elements)
├── calibration.py                 # CalibrationProfile model, YAML loader, built-in defaults
└── explainer.py                   # Explainability breakdown builder

specmetrics/plugins/calibration/   # New calibration plugin (shared across measurement methods)
├── __init__.py
├── plugin.py                      # CalibrationPlugin, CalibrationHandler, create_metadata()
├── loader.py                      # YAML file discovery and loading from .specmetrics/calibration/
├── validator.py                   # Calibration profile validation
└── models.py                      # CalibrationProfile base model

tests/
├── unit/
│   ├── test_token_points_calculator.py      # Core calculation logic
│   ├── test_token_points_calibration.py     # Calibration loading, defaults, overrides
│   └── test_token_points_models.py          # Model construction, serialization
├── contract/
│   └── test_token_points_measurement.py     # Measurement API contract
└── integration/
    └── test_token_points_pipeline.py        # Full pipeline: CFM + CSM → Token Points
```

**Structure Decision**: Follows existing measurement plugin convention (`plugins/measurement/<method>/`). Calibration is extracted as a shared plugin (`plugins/calibration/`) following the Rule Pack plugin pattern — calibration profiles affect all measurement methods, not just Token Points.

## Complexity Tracking

*No constitution violations to justify.*
