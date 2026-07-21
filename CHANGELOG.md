# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [0.5.0] — 2026-07-21

### [034-improve-deterministic-extraction](specs/034-improve-deterministic-extraction) Improve Deterministic Extraction Engine — operation extraction, SNAP semantic markers, and actor identification

#### Added

- Add `gwt-given-operation`, `gwt-when-operation`, `gwt-then-operation` rules with `type: "operation"` in `default_rule_pack.yaml`
- Change 4 Speckit GWT rules from `type: "fact"` to `type: "operation"` in `speckit_rules.yaml`
- Add `_infer_semantic_marker()` function in CFM builder — maps elements to SNAP categories via section context
- Expand `ACTOR_PATTERNS` with stakeholder, moderator, subscriber, visitor, guest, consumer, provider, vendor, partner keywords
- Add section-context actor detection in classifier — entities from Actor/Role/User/Persona sections classified as actors
- Add key-phrase actor detection — entity text containing "acts as", "is a user", "represents a person", or "external system" classified as actor
- Make section-to-semantic-marker mappings overridable via rule packs

### [035-openspec-operation-rules](specs/035-openspec-operation-rules) OpenSpec Operation Extraction Rules — repurpose 9 fact rules to operation type

#### Added

- Change `openspec-then-assertion`, `openspec-and-clause`, `openspec-shall-statement`, `openspec-deve-statement`, `openspec-req-heading`, `openspec-task-item`, `openspec-task-category`, `openspec-decision-colon`, `openspec-what-changes` from `type: "fact"` to `type: "operation"` in `openspec_rules.yaml`
- Fix regex patterns in 7 non-matching OpenSpec rules to align with observation-based extraction format

### [036-measure-metrics-breakdown](specs/036-measure-metrics-breakdown) Measure Metrics Breakdown — per-entity score breakdowns in `metrics.json`

#### Added

- Add `MetricBreakdownEntry` and `EntityScore` Pydantic models with `CanonicalEntityType` Literal
- Add `measurement_result_raw` field to `PipelineResult` dataclass
- Create `EntityScoreBuilder` class with per-metric build methods for all 8 metrics
- Create `MetricBreakdownBuilder.build_all()` producing `list[MetricBreakdownEntry]`
- Create `save_metrics_json()` function writing `metrics.json` with UTF-8 pretty-printed JSON
- Add entity serialization to all 8 measurement handler payloads (fpa, sfp, snap, bcp, storypoints, token_points, cognitive_points, tshirt)
- Enrich entity metadata with metric-specific details (complexity ratings, factor breakdowns, bloom levels, weights)
- Implement schema validation ensuring uniform top-level and entity-level keys across all metric types
- Handle edge cases: empty project, missing measurement_result_raw, metric filter exclusion
- Create unit and integration tests for `EntityScoreBuilder`, `MetricBreakdownBuilder`, and schema validation

### [037-llm-batch-rate-limit](specs/037-llm-batch-rate-limit) LLM Batch Processing & Rate Limiting — unified gateway with batching, rate limiting, and JSON structured output

#### Added

- Create `LLMGateway` class with `complete()` and `complete_batch()` methods — unified gateway for all LLM calls
- Create `RateLimiter` class with sliding-window deque algorithm and configurable RPM limit (default 15)
- Create `LLMCallRecord`, `BatchRequest`, `DocumentPayload` models for call tracking and batch assembly
- Implement batch size splitting when `batch_max_chars` exceeded
- Implement partial batch failure handling — retry missing documents individually
- Add `--llm-rpm-limit` CLI parameter to `measure` command (0 = unlimited)
- Read `SPECMETRICS_LLM_RPM_LIMIT` environment variable as fallback config
- Implement JSON structured output mode — `response_format={"type": "json_object"}` for OpenAI-compatible providers
- Implement JSON mode fallback for non-OpenAI providers with system prompt instruction
- Remove `_strip_code_fence()` calls and regex-based response cleaning
- Handle JSON parse failure with retry and fallback to deterministic extraction
- Handle Ctrl+C during rate-limited wait with clean exit
- Add LLM call summary stats (total calls, total tokens, total duration) to `PipelineResult`

### [038-token-points-improvements](specs/038-token-points-improvements) Token Points Improvements — content-based token estimation with tiktoken integration

#### Added

- Add `content_token_count` and `content_score` fields to `TokenContribution` model
- Add `content_multiplier` field to `CalibrationProfile` (default 0.1)
- Add non-zero default weights for Specification Activities and References in calibration
- Create `count_tokens()` function with tiktoken (`cl100k_base`) and character-count fallback
- Implement content-based scoring formula: `score = type_weight + (content_tokens × content_multiplier)`
- Extract content text per element: `name + " " + description` for CSM/CFM elements
- Add content token counts and content multiplier to handler payload

### [039-cognitive-points-improvements](specs/039-cognitive-points-improvements) Cognitive Points Improvements — content-based cognitive effort estimation and sub-type Bloom classification

#### Added

- Add `content_token_count` and `content_score` fields to `CognitiveContribution` model
- Add `content_multiplier` field to `CognitiveCalibrationProfile` (default 0.1)
- Implement sub-type Bloom classification with 3-tier lookup (sub-type → base type → default)
- Add sub-type Bloom mappings for 4 BusinessRule sub-types and 4 Operation sub-types
- Change default Bloom level from "analyze" (4.0) to "understand" (2.0) for conservative scoring
- Implement content-based scoring: `score = bloom_weight + (content_tokens × content_multiplier)`
- Extract `count_tokens()` into shared `kernel/token_utils.py` utility

### [040-story-points-improvements](specs/040-story-points-improvements) Story Points Improvements — content-aware estimation with CSM coverage and relative ranking

#### Added

- Rename `FunctionalWorkItem` to `WorkItem` with new fields: `element_type`, `source_model`, `structural_score`, `content_tokens`, `content_score`, `rank_position`, `base_weight`
- Add `total_raw_score`, `specification_effort_total`, `implementation_effort_total`, `content_multiplier`, `content_tokens_by_type`, `calibration_version` to `StoryPointMeasurementResult`
- Create `StoryPointsCalibrationProfile` model with all configurable fields and defaults
- Implement `load_calibration()` loading and merging YAML calibration files
- Implement content-based estimation: `raw_score = structural_score + content_score`
- Implement relative ranking normalization — entities sorted by raw score and mapped proportionally to Modified Fibonacci scale
- Expose cross-specification comparability data in output payload

### [041-tshirt-sizing](specs/041-tshirt-sizing) T-Shirt Sizing Improvements — corrected mapping table and output fixes

#### Added

- Update `DEFAULT_MAPPING` in classifier: M=(5,5), L=(8,13), XL=(20,40), XXL=(100,100) — all 9 Fibonacci values covered without gaps
- Fix `measure.json` output: `total` shows actual entity count (was 0), add `breakdown` with per-size counts
- Fix `metrics.json` output: use `unit: "entities"` and include per-entity T-shirt classifications with mapping metadata
- Fix CLI display to show entity count and per-size breakdown line

[Unreleased]: https://github.com/amaurycarvalho/specmetrics/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/amaurycarvalho/specmetrics/releases/tag/v0.5.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.