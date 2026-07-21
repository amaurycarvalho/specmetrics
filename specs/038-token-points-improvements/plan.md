# Implementation Plan: Token Points Improvements

**Branch**: `038-token-points-improvements` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/038-token-points-improvements/spec.md`

## Summary

Enhance the Token Points measurement engine with content-based token estimation, replacing the current flat-weight-per-element approach. Each element's score becomes `type_weight + (content_token_count × content_multiplier)`, grounding the metric in actual specification text volume. Additionally, update the default calibration profile with non-zero Specification Activity weights and a positive References weight, and document the methodology in RFC-028.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: tiktoken (optional, for exact GPT-4 token counting; fallback to character-count heuristic), Pydantic v2 (updated models), structlog (per-element content token logging)

**Storage**: No new storage — calibration YAML files in `.specmetrics/calibration/` (existing directory)

**Testing**: pytest

**Target Platform**: Linux (CLI)

**Project Type**: Measurement engine enhancement

**Performance Goals**: Content tokenization adds ≤ 50ms overhead for 500 elements (tiktoken is fast; fallback even faster)

**Constraints**: Backward-compatible calibration YAML format; same formula structure (SpecificationCost + CodeGenerationCost); no changes to extraction pipeline or canonical models

**Scale/Scope**: Single measurement engine (`token_points`); 3 modified files + 1 calibration model + 1 RFC document

## Constitution Check

*GATE: Must pass before Phase 0 research.*

**Engaged Principles**:
- Principle IV (LLM-Assisted, Deterministic Results): Token counting is deterministic; improved engine remains deterministic
- Principle V (Evidence First): Content token counts are evidence for scores — logged per element
- Principle VI (Explainability by Design): Formula `type_weight + content_score` is transparent and auditable
- Principle VII (Canonical Representation): Operates on CSM/CFM; no framework coupling
- Principle IX (Rule Externalization): Calibration weights and content_multiplier in external YAML
- Principle XIII (Evolution Without Disruption): Old calibration files continue to work; new content-based component is additive

**Compliance Verifications**:
- [x] Deterministic Results: Same models + same calibration + same content → same score
- [x] Evidence First: `content_token_count` field logged per TokenContribution
- [x] Explainability by Design: Each element's score decomposes to type_weight + content_score
- [x] Canonical Representation: No changes to CSM, CFM, or extraction pipeline
- [x] Rule Externalization: content_multiplier and all weights in calibration YAML
- [x] Layer Independence: Changes contained within token_points engine; plugin interface unchanged

## Project Structure

### Documentation (this feature)

```text
specs/038-token-points-improvements/
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
│   ├── measurement/token_points/
│   │   ├── calculator.py         # MODIFY: add token counting + new score formula
│   │   ├── models.py             # MODIFY: add content_token_count, content_score to TokenContribution
│   │   └── plugin.py             # MODIFY: extend payload with content token counts
│   └── calibration/
│       ├── models.py             # MODIFY: add content_multiplier, activity defaults, references weight
│       └── validator.py          # MODIFY: validate content_multiplier >= 0
├── tests/
│   └── test_token_points_content.py  # NEW: content-based estimation tests
├── docs/rfcs/
│   └── RFC-028 - Token Points Measurement Engine.md  # MODIFY: add content-based estimation section
```

**Structure Decision**: No new directories. Changes are tightly scoped to the token_points engine and calibration models. The RFC update is a documentation change in `docs/rfcs/`.

## Complexity Tracking

> No constitution violations.

## Design Decisions

### 1. Score Formula

**Decision**: `score = type_weight + (content_token_count × content_multiplier)` with `content_multiplier` defaulting to 0.1.

This keeps content contribution at the same order of magnitude as type weights: a 100-token description contributes 10.0 (comparable to a functional_process type weight of 5.0). The content_multiplier can be tuned via calibration YAML.

### 2. Tokenizer Strategy

**Decision**: Use tiktoken (`cl100k_base`) if installed; fall back to `len(text) // 4` if not. The engine imports tiktoken lazily — if the import fails, it uses the character-count heuristic with a warning log.

Rationale: tiktoken is the standard GPT tokenizer and produces exact token counts. The fallback avoids a hard dependency while still providing estimation.

### 3. Content Sources Per Element

**Decision**: Tokenize the concatenation of `name + " " + description` for each element. CSM elements use their `description` field; CFM elements use `name` + `description` (or `name` only if no description). For elements stored as dicts (relationships), use the element's `id` as name and empty description.

### 4. Calibration Backward Compatibility

**Decision**: The `CalibrationProfile` Pydantic model uses `Field(default=...)` for new fields. When loading old YAML files that lack `content_multiplier`, `references`, or `activities`, the Pydantic defaults fill in. Old calibration files producing 0.0 for activities now produce the new defaults. This is intentional — the spec explicitly requires activities to have non-zero defaults (SC-002).

### 5. Payload Extension

**Decision**: Add `token_content_tokens` (dict of element_type → total content tokens) and `token_content_multiplier` to the existing payload. The `token_element_counts` dict extended with `content_tokens` per element type. This enables SC-003 verification.
