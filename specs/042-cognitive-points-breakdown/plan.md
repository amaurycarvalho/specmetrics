# Implementation Plan: Cognitive Points Breakdown

**Branch**: `042-cognitive-points-breakdown` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/042-cognitive-points-breakdown/spec.md`

## Summary

Add a Bloom-level score breakdown to the Cognitive Points output in two places: (1) a `breakdown` field in the `measure.json` stage artifact, and (2) indented lines in the CLI text display below the Cognitive Points total. The breakdown aggregates `partial_score` by `bloom_level` across all `CognitiveContribution` entities — data already computed within the plugin. No changes to measurement formulas, data models, or calibration profiles.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Pydantic v2 (models are read, not modified)

**Storage**: No new storage — `measure.json` layout gains one new optional field per metric entry

**Testing**: pytest

**Target Platform**: Linux (CLI)

**Project Type**: Measurement engine output enhancement

**Performance Goals**: Negligible overhead — the breakdown is computed in O(n) on the existing `all_cognitive_contributions` list (already built)

**Constraints**: Additive only — no changes to existing payload keys, data models, calibration profiles, or plugin interface

**Scale/Scope**: 3 files modified (plugin.py, orchestrator.py, formatters.py); no new files in source tree

## Constitution Check

*GATE: Must pass before Phase 0 research.*

**Engaged Principles**:
- Principle VI (Explainability by Design): The breakdown exposes how each Bloom level contributes to total cognitive effort, making the measurement more explainable
- Principle VII (Canonical Representation): Operates on CSM/CFM-derived CognitiveContribution data; no framework coupling
- Principle VIII (Plugin-Oriented Architecture): Aggregation computed within the cognitive_points plugin; orchestrator and CLI consume the new payload key
- Principle XI (Observability as a Native Capability): Enriches measure.json with more granular cognitive profile data
- Principle XIII (Evolution Without Disruption): New fields are additive; existing consumers ignore unknown keys

**Compliance Verifications**:
- [x] Deterministic Results: Same contributions → same breakdown; no LLM or randomness involved
- [x] Evidence First: Breakdown derives from existing CognitiveContribution entities with evidence refs
- [x] Explainability by Design: Each level's contribution is directly visible in both measure.json and CLI
- [x] Canonical Representation: No changes to CSM, CFM, or extraction pipeline
- [x] Plugin-Oriented: Breakdown computed inside the plugin, exposed via standard payload dict
- [x] Layer Independence: Plugin adds payload key; orchestrator maps it; CLI reads it — no cross-layer coupling
- [x] Open by Default: measure.json schema is self-documenting; breakdown format follows existing patterns

## Project Structure

### Documentation (this feature)

```text
specs/042-cognitive-points-breakdown/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
specmetrics/
├── plugins/
│   └── measurement/cognitive_points/
│       └── plugin.py                # MODIFY: compute cognitive_bloom_breakdown payload key
├── application/
│   └── orchestrator.py              # MODIFY: map breakdown key in measure stage entities
├── cli/
│   └── formatters.py                # MODIFY: display breakdown below Cognitive Points line
└── tests/
    ├── unit/test_cognitive_points_calculator.py  # MODIFY: add breakdown aggregation tests
    └── integration/test_cognitive_points_pipeline.py  # MODIFY: add breakdown presence tests
```

**Structure Decision**: No new directories or files in source. Changes are confined to 3 existing files in the plugin, orchestrator, and CLI layers. Tests extend existing test files.

## Complexity Tracking

> No constitution violations.

## Design Decisions

### 1. Breakdown Aggregation Source

**Decision**: Compute the breakdown from `all_cognitive_contributions` (already assembled in `plugin.py:handle()` by concatenating spec and func contributions). Group by `bloom_level`, sum `partial_score`.

Rationale: The contributions list is the authoritative source for per-element Bloom level and score. No need for a separate pass or new data structure.

### 2. Payload Key Format

**Decision**: New key `cognitive_bloom_breakdown` with value `dict[str, float]` — e.g., `{"understand": 890.0, "apply": 1500.0}`. Only levels with non-zero total appear.

Rationale: Flat dict avoids nested `{level: {total: X}}` in the payload. The measure.json builder wraps it into the `{level: {total: X}}` format to match the user's requested output shape.

### 3. measure.json Format

**Decision**: The `breakdown` field in measure.json uses `{level: {total: float}}` format (nested dict), matching the user's requested format:
```json
"breakdown": {
  "understand": {"total": 890.0},
  "apply": {"total": 1500.0}
}
```

Rationale: The wrapping from flat dict to nested dict is done in the orchestrator to keep the payload simple while producing the requested measure.json shape. This follows the pattern used by `tshirt_breakdown` which also transforms payload data for output.

### 4. CLI Display Format

**Decision**: Indented lines below Cognitive Points total, format `    {Level}: {total}` using capitalized level name and the float value. No sub-indentation or tree characters.

Rationale: Matches the user's requested output format. Simple indentation with 4 spaces distinguishes breakdown lines from the parent metric line without adding visual noise from tree-drawing characters (used by Function Points for its hierarchical breakdown).

### 5. Empty/Zero Handling

**Decision**: Exclude levels with zero total score from both payload and display. An empty spec produces `cognitive_bloom_breakdown: {}` in the payload and no indented lines in the CLI.

Rationale: Zero-total levels are noise. Excluding them keeps output clean and prevents misreading empty levels as relevant data.

### 6. Ordering

**Decision**: Display Bloom levels in order of cognitive complexity: Remember, Understand, Apply, Analyze, Evaluate, Create. The data dict itself uses standard dict ordering (which is insertion order in Python 3.7+).

Rationale: Fixed Bloom taxonomy hierarchy is well-known and stable. Ordering by cognitive complexity is more meaningful than alphabetical.
