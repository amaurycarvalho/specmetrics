# Research: Story Points Improvements

**Feature**: 040-story-points-improvements  
**Date**: 2026-07-21

## 1. Content Token Counting

**Decision**: Reuse the existing `count_tokens()` from `specmetrics.kernel.token_utils`.

**Rationale**: Token Points and Cognitive Points already consume this shared utility. It uses `tiktoken` with the `cl100k_base` encoding (GPT-4/GPT-3.5 tokenizer) and falls back to `max(1, len(text) // 4)` when `tiktoken` is unavailable. No new dependency or algorithm needed.

**Alternatives considered**:
- Custom tokenization per plugin: rejected — violates DRY and shared-kernel principles.
- Word count instead of tokens: rejected — tokens provide finer granularity and are already established in the codebase.

## 2. CSM Integration Pattern

**Decision**: Extend `StoryPointsHandler` to subscribe to both `EventType.CANONICAL_SPEC_MODEL_BUILT` and `EventType.CANONICAL_MODEL_BUILT`, collecting both CSM and CFM before triggering measurement.

**Rationale**: The current handler subscribes to `EventType.MEASUREMENT_COMPLETED` and extracts the CFM from the pipeline context. The CSM is already available in `PipelineContext.canonical_spec_model`. The handler should wait until both models are available, then invoke the calculator with both.

**Alternatives considered**:
- Two separate measurement events (one for CSM, one for CFM): rejected — Story Points is a unified metric; splitting would complicate aggregation.
- CSM-only measurement: rejected — CFM functional processes are the primary estimation targets.

## 3. Relative Ranking Normalization Algorithm

**Decision**: Replace fixed-threshold bucket mapping with percentile-band ranking across the 9 Modified Fibonacci values.

**Algorithm**: Given N entities with raw scores `s_1 ≤ s_2 ≤ ... ≤ s_N`:

1. Sort all entity raw scores in ascending order.
2. Divide the sorted list into 9 equal-proportion bands (each containing approximately N/9 entities).
3. Map bands to Fibonacci values:
   - Band 0 (lowest ~11.1%): normalized_value = 1
   - Band 1 (next ~11.1%): normalized_value = 2
   - Band 2: normalized_value = 3
   - Band 3: normalized_value = 5
   - Band 4: normalized_value = 8
   - Band 5: normalized_value = 13
   - Band 6: normalized_value = 20
   - Band 7: normalized_value = 40
   - Band 8 (highest ~11.1%): normalized_value = 100

When N < 9 (fewer entities than bands), use direct rank-to-Fibonacci mapping: the lowest raw score gets 1, the highest gets 100, intermediates get proportional Fibonacci values.

**Rationale**: This makes Story Points a genuine relative metric — "this element represents more implementation effort than that element within this specification." The Fibonacci scale provides the classic non-linear sizing that matches human estimation psychology (uncertainty grows with size).

**Alternatives considered**:
- Keep fixed thresholds with recalibrated values: rejected — the user explicitly requested relative scoring where lower raw scores map to lower Fibonacci values and vice versa, regardless of absolute magnitude.
- Standard deviation-based bucketing: rejected — more complex to explain and less intuitive than percentile bands.
- Configurable band count: considered for future, but 9 bands (matching the 9 Fibonacci values) is the default.

## 4. Calibration Profile Design

**Decision**: Follow the Token Points pattern — use the shared calibration infrastructure (`specmetrics.plugins.calibration`) rather than defining standalone calibration models like Cognitive Points does.

**Rationale**: Token Points' `CalibrationProfile` already contains `content_multiplier` and type-specific weights (`SpecificationCostWeights`, `CodeGenerationCostWeights`). Story Points can extend this pattern with its own calibration profile class that adds factor coefficients and ranking strategy configuration. This keeps calibration discoverable and consistent.

**New calibration fields**:

| Field | Type | Default | Description |
|---|---|---|---|
| `version` | `str` | `"1.0"` | Profile format version |
| `content_multiplier` | `float` | `0.1` | Content token weight multiplier |
| `factor_coefficients` | `dict[str, float]` | 6 defaults | Per-factor weights for FP scoring |
| `csm_base_weights` | `dict[str, float]` | 13 defaults | CSM element type base weights |
| `cfm_base_weights` | `dict[str, float]` | 5 defaults | Non-FP CFM element base weights |
| `default_fallback_weight` | `float` | `1.0` | Weight for unknown element types |
| `fibonacci_scale` | `list[int]` | `[1,2,3,5,8,13,20,40,100]` | Output Fibonacci values |
| `ranking_strategy` | `str` | `"percentile"` | Band distribution strategy |

**Alternatives considered**:
- Standalone calibration (Cognitive Points pattern): rejected — the shared calibration infrastructure provides discovery, loading, merging, and validation that would need to be duplicated.
- Inline defaults only (current Story Points pattern): rejected — rules must be externalizable per Principle IX.

## 5. Normalizer Rewrite

**Decision**: Rewrite `normalizer.py` to replace the `FibonacciNormalizer` class (fixed thresholds: `[2,4,8,14,22,35,55,85]`) with a `RelativeRankingNormalizer` that implements the percentile-band algorithm.

**Key changes**:
- Remove `_DEFAULT_THRESHOLDS` and threshold-based `normalize()` logic.
- New `normalize(raw_scores: list[float]) -> dict[str, int]` method that accepts all entity raw scores and returns a mapping of element_id to normalized Fibonacci value.
- Configurable `fibonacci_scale` and `ranking_strategy` from calibration.
- Preserve the `NormalizationResult` output concept but adapt it to include ranking position.

**Rationale**: The threshold-based model is fundamentally incompatible with relative scoring. Clean rewrite avoids confusing legacy code.

**Alternatives considered**:
- Add ranking as a parallel normalization mode: rejected — adds complexity, and fixed thresholds have no use case after this feature.

## 6. Backward Compatibility Strategy

**Decision**: When `content_multiplier = 0.0`, produce raw scores identical to the current factor-only engine. Old calibration profiles (without new fields) load with defaults.

**Implementation**:
- `content_multiplier = 0.0`: content-based contribution is zero. Non-FP elements still get base weights (this is new behavior, but it's gated by whether CSM data is provided — if no CSM exists, only FP estimation runs).
- Calibration loading: use Pydantic `Field(default=...)` for all new profile fields. Old YAML files missing these keys will load with defaults.
- Old test fixtures: continue to pass when `content_multiplier = 0.0` and no CSM is provided.

## 7. Output Payload Extensions

**Decision**: Extend `StoryPointMeasurementResult` with the fields specified in FR-010 without breaking the existing payload contract.

**New payload fields**:
- `content_multiplier: float` — the multiplier used for this run
- `specification_effort_total: float` — sum of raw scores from CSM elements
- `implementation_effort_total: float` — sum of raw scores from CFM elements
- `content_tokens_by_type: dict[str, int]` — per-element-type token totals

Per-element additions to `FunctionalWorkItem` (to be renamed or extended):
- `content_tokens: int` — token count for this element
- `content_score: float` — `content_tokens * content_multiplier`
- `structural_score: float` — the factor/base-weight portion
- `raw_score: float` — `structural_score + content_score` (existing field, repurposed)

## 8. RFC-041 Documentation

**Decision**: Create `docs/rfcs/RFC-041 - Story Points Measurement Engine.md` following the pattern established by RFC-028 (Token Points) and RFC-029 (Cognitive Points).

**Sections**: Methodology overview, factor definitions, element coverage tables, normalization algorithm, calibration reference, cross-specification comparison guidance, Kanban use case appendix.
