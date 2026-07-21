# Implementation Plan: Story Points Improvements

**Branch**: `040-story-points-improvements` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/040-story-points-improvements/spec.md`

## Summary

Extend the Story Points measurement engine from CFM-only structural factor estimation to a comprehensive relative effort metric covering all CSM and CFM element types. Add content-based estimation (token counting) as an additive component to the existing 6-factor weighted sum. Replace fixed-threshold Fibonacci normalization with relative ranking: entities are sorted by raw score and mapped proportionally to the Modified Fibonacci scale (1, 2, 3, 5, 8, 13, 20, 40, 100). Expose cross-specification comparability data in the output payload. Make all weights and coefficients configurable via calibration profiles. Create RFC-041 documenting the complete methodology.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Pydantic v2 (models), tiktoken (token counting, with fallback), structlog (logging), pytest (testing)

**Storage**: N/A (stateless computation; calibration profiles as YAML files)

**Testing**: pytest >= 8.0.0 with `tests/unit/`, `tests/contract/`, `tests/integration/` directories

**Target Platform**: Linux (CLI tool, local execution)

**Project Type**: CLI measurement plugin

**Performance Goals**: < 5 seconds for 500+ elements; linear scaling with element count

**Constraints**: Deterministic output (same inputs → same results), backward-compatible calibration loading, plugin isolation (depends only on kernel contracts)

**Scale/Scope**: Typical specification files contain 10-200 elements across CSM + CFM

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: IV, V, VI, VII, VIII, IX, XIII, XIV

**Compliance Verifications**:

- [x] **Specification First**: Primary input is the Canonical Functional Model (CFM) and, newly, the Canonical Specification Model (CSM) — both derived from software specifications.
- [x] **Evidence First**: Every element contribution preserves `EvidenceRef` references to source specification text. Content token counts and factor breakdowns are traceable per element.
- [x] **Canonical Representation**: The engine operates exclusively on CFM and CSM canonical models. Framework-specific concepts (SpecKit, OpenSpec) are already normalized before estimation.
- [x] **Plugin-Oriented**: All changes reside within the existing Story Points measurement plugin (`specmetrics/plugins/measurement/storypoints/`). No changes to kernel, adapters, or other plugins.
- [x] **Rule Externalization**: Factor coefficients, element base weights, content multiplier, Fibonacci scale values, and ranking strategy are externalized in calibration profiles (YAML).
- [x] **Layer Independence**: Story Points consumes only CFM and CSM via their public model contracts. It does not depend on extraction providers, adapters, or exporters.
- [x] **Open by Default**: Measurement formulas are documented in RFC-041. Calibration profile schema is documented. Output payload fields are defined.

## Project Structure

### Documentation (this feature)

```text
specs/040-story-points-improvements/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── calibration-profile.md  # Calibration profile YAML schema
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
specmetrics/plugins/measurement/storypoints/
├── __init__.py           # Public exports
├── plugin.py             # StoryPointsPlugin, StoryPointsHandler (modified)
├── models.py             # Data models (modified: new fields, new entities)
├── calculator.py         # Core estimation engine (modified: CSM + content + ranking)
├── factor_scorer.py      # Six-factor weighted scoring (unchanged)
├── normalizer.py         # Normalization (rewritten: rankings → Fibonacci)
├── calibrator.py         # NEW: Calibration loading & management
├── explainer.py          # Explanation helpers (modified)
└── token_counter.py      # NEW: Content token counting wrapper

tests/
├── unit/
│   ├── test_storypoints_models.py          # Modified: new model fields
│   ├── test_storypoints_factor_scorer.py   # Unchanged
│   ├── test_storypoints_calculator.py      # Modified: CSM inputs, ranking tests
│   ├── test_storypoints_normalizer.py      # Rewritten: ranking normalization
│   ├── test_storypoints_calibrator.py      # NEW: calibration tests
│   └── test_storypoints_token_counter.py   # NEW: token counting tests
├── contract/
│   └── test_storypoints_measurement.py     # Modified: new payload contract
└── integration/
    └── test_storypoints_pipeline.py        # Modified: CSM + CFM pipeline
```

**Structure Decision**: Single plugin package under `specmetrics/plugins/measurement/storypoints/`. No new top-level directories. New files (`calibrator.py`, `token_counter.py`) added within the existing plugin package. Test files follow the existing `tests/unit/`, `tests/contract/`, `tests/integration/` convention.

## Complexity Tracking

> No constitution violations. All changes are additive and backward-compatible within the existing plugin architecture.
