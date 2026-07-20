# Implementation Plan: Populate Stage Entities on Run Artifacts

**Branch**: `032-populate-stage-entities` | **Date**: 2026-07-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/032-populate-stage-entities/spec.md`

## Summary

Populate the `entities` field in each stage JSON artifact (`.specmetrics/runs/<id>/*.json`) with the actual data each pipeline stage identified. Currently only `measure.json` has populated entities — all other stages produce `"entities": []`. The feature adds per-stage entity serialization in `_serialize_stage_data()`, extends `PipelineResult` to carry entity data, and makes the truncation limit configurable via `config.yml`.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: structlog, pydantic v2, typer, NetworkX, ruamel.yaml

**Storage**: Filesystem — `.specmetrics/runs/<run_id>/*.json` (per-stage artifacts), `.specmetrics/evidence_graphs/<run_id>.jsonl` (graph store), `.specmetrics/output/specmetrics-output.json` (main output)

**Testing**: pytest, ruff (linting)

**Target Platform**: Linux, macOS, WSL — local CLI execution

**Project Type**: CLI tool (specmetrics)

**Performance Goals**: Stage entity serialization up to 5000 entities completes within 500ms per stage; per-file artifact ≤ ~5MB for richly detailed entities

**Constraints**: Backward compatibility with existing `entities: []` files; additive field changes only; `count` field always reflects full total (not truncated); 200-char truncation on text/content fields

**Scale/Scope**: 8 pipeline stages × up to 5000 entities per stage (configurable); 100k+ total entities possible with truncation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: V (Evidence First), VI (Explainability by Design), VII (Canonical Representation), VIII (Plugin-Oriented), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First: Not directly engaged — this feature consumes pipeline outputs, not specifications themselves.
- [x] Evidence First: Design preserves traceability by including document_id, section_id, and text evidence references in every entity where applicable.
- [x] Canonical Representation: CSM and CFM entities are serialized in their canonical form (CanonicalSpecificationModel and CanonicalFunctionalModel), not adapter-specific formats.
- [x] Plugin-Oriented: Extract stage entities accommodate arbitrary ExtractionProvider plugins via generic type/confidence/content schema rather than provider-specific fields.
- [x] Rule Externalization: Not directly engaged — Rule Pack application is summarized (descriptive), not modified.
- [x] Layer Independence: Each stage's entity serialization is independent; discover entities don't depend on extraction/graph data. The serialization only reads stage outputs — it doesn't introduce cross-layer coupling.
- [x] Open by Default: JSON artifacts are standard JSON — no proprietary format. Schema is documented in data-model.md.

## Project Structure

### Documentation (this feature)

```text
specs/032-populate-stage-entities/
├── spec.md              # Feature specification (/speckit.specify)
├── plan.md              # This file (/speckit.plan)
├── research.md          # Phase 0 — resolved unknowns
├── data-model.md        # Phase 1 — entity schemas and relationships
├── quickstart.md        # Phase 1 — validation guide
└── contracts/           # Phase 1 — interface contracts
    └── stage-artifact-schema.md
```

### Source Code (repository root)

```text
specmetrics/
├── application/
│   ├── models.py              # + StageEntities, + stage_entities field on PipelineResult
│   └── orchestrator.py        # Modify _serialize_stage_data, add build_stage_entities
├── infrastructure/
│   └── config/
│       └── schema.py          # + RunArtifactsSettings
└── cli/
    └── output_models.py       # + StageEntityItem (if needed for main export)

tests/
├── unit/
│   ├── test_serialize_stage_data.py
│   └── test_truncation.py
└── integration/
    └── test_run_artifacts.py
```

**Structure Decision**: Single project layout. Changes are concentrated in `application/` (models + orchestrator), `infrastructure/config/` (schema), and `cli/` (output models). Testing follows existing `tests/unit/` and `tests/integration/` convention.

## Complexity Tracking

No complexity violations. The feature changes are limited to the serialization layer (orchestrator.py) and data model (models.py) — no architectural complexity is introduced.
