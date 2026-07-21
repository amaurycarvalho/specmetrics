# Implementation Plan: T-Shirt Sizing Improvements

**Branch**: `041-tshirt-sizing` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/041-tshirt-sizing/spec.md`

## Summary

Correct the T-Shirt Sizing measurement plugin's default mapping table to distribute the 9 Modified Fibonacci values evenly across the 6 T-shirt sizes (XS=[1], S=[2,3], M=[5], L=[8,13], XL=[20,40], XXL=[100]). Fix the measure.json output so `total` shows the actual entity count (currently 0) and add a `breakdown` with per-size counts. Fix the metrics.json output to use `unit: "entities"` and include per-entity T-shirt classifications with mapping metadata. Fix the CLI display to show the entity count and per-size breakdown line. Create RFC documentation in `docs/rfcs/`.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Pydantic v2 (models), structlog (logging), pytest (testing)

**Storage**: N/A (stateless classification; mapping can be loaded from YAML configuration)

**Testing**: pytest >= 8.0.0 with `tests/unit/test_tshirt_*.py`, `tests/contract/test_tshirt_measurement.py`, `tests/integration/test_tshirt_pipeline.py`

**Target Platform**: Linux (CLI tool, local execution)

**Project Type**: CLI measurement plugin (existing)

**Performance Goals**: O(n) lookup-table classification; < 1s for 1000+ entities

**Constraints**: Deterministic output (same Story Point value → same T-shirt size), configurable mapping, backward-compatible payload changes

**Scale/Scope**: Typical specifications produce 10–200 classified entities

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: IV, V, VI, VII, VIII, IX, XIII, XIV

**Compliance Verifications**:

- [x] **Specification First**: T-Shirt Sizing consumes Story Points results derived from software specifications.
- [x] **Evidence First**: Each classified entity preserves its Story Point value, T-shirt size, and the mapping rule applied. Evidence is traceable.
- [x] **Canonical Representation**: T-Shirt operates on the Story Points pipeline result. It does not depend on SpecKit, OpenSpec, or any framework-specific format.
- [x] **Plugin-Oriented**: All changes reside within the existing T-Shirt plugin at `specmetrics/plugins/measurement/tshirt/`. Orchestrator and formatter changes are minimal wiring fixes.
- [x] **Rule Externalization**: The mapping table (Story Point ranges → T-shirt sizes) is a configurable list of `TShirtSize` entries. Custom mappings override the default.
- [x] **Layer Independence**: T-Shirt depends only on Story Points result from the pipeline context. No dependency on extraction providers, adapters, or exporters.
- [x] **Open by Default**: Mapping table, output formats, and methodology are documented in the RFC.

## Project Structure

### Documentation (this feature)

```text
specs/041-tshirt-sizing/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── mapping-schema.md    # TShirtSize mapping configuration schema
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
specmetrics/plugins/measurement/tshirt/
├── __init__.py           # Public exports
├── plugin.py             # TShirtHandler, TShirtPlugin (modified: payload keys)
├── models.py             # Pydantic models (unchanged)
├── classifier.py         # TShirtClassifier (modified: DEFAULT_MAPPING values)
├── explainer.py          # Explanation helpers (unchanged)

specmetrics/application/
├── orchestrator.py       # Pipeline orchestrator (modified: tshirt key mapping)
├── models.py             # Metric name/display maps (verify tshirt mapping)
├── metrics_json.py       # metrics.json builder (modified: unit, entity fields)

specmetrics/cli/
├── formatters.py         # Text result formatter (modified: tshirt display)

tests/
├── unit/
│   ├── test_tshirt_classifier.py   # Modified: new mapping ranges
│   └── test_tshirt_models.py       # Unchanged (existing tests)
├── contract/
│   └── test_tshirt_measurement.py  # Modified: payload contract
└── integration/
    └── test_tshirt_pipeline.py     # Modified: integrated output checks

docs/rfcs/
└── RFC-XXX - T-Shirt Sizing.md     # NEW: T-Shirt methodology documentation
```

**Structure Decision**: Changes are focused on the existing T-Shirt plugin package with minor wiring fixes in the application orchestrator and CLI formatter. No new plugin modules needed. The RFC document follows the established `docs/rfcs/` pattern.

## Complexity Tracking

> No constitution violations. All changes are corrective fixes to existing behavior (mapping values, output integration, display formatting).
