# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] — 2026-07-17

### [021-canonical-specification-model](specs/021-canonical-specification-model) Canonical Specification Model Builder — transforms EvidenceGraph into a framework-independent CanonicalSpecificationModel

#### Added

- Create `specmetrics/kernel/csm/` package directory with `__init__.py`
- Add `CANONICAL_SPECIFICATION_MODEL_BUILT` to `EventType` enum and `canonical_spec_model` field to `PipelineContext`
- Create `EvidenceRef`, `CsmElement` base, `BuildMetadata`, `ClassificationConflict`, and all 8 CSM entity models
- Create `CanonicalSpecificationModel` root model with query interface methods
- Create deterministic classifier with regex patterns for all 8 canonical categories
- Create SpecificationActivity type detector and evidence graph traversal helpers
- Implement `build()` function that transforms EvidenceGraph → CanonicalSpecificationModel
- Implement `CsmBuilderStage` handler class and stage plugin metadata registration
- Implement query interface, `CsmConsumer` protocol, serialization round-trip, framework-label stripping
- Add UUID v4 and non-empty validators to `CsmElement`
- Add unit, contract, and integration tests for all user stories

#### Changed

- Update `CANONICAL_EVENT_ORDER` — insert `CANONICAL_SPECIFICATION_MODEL_BUILT` after `EVIDENCE_GRAPH_BUILT`
- Refactor `_find_linked()` to two-pass approach for symmetric cross-activity linking
- Remove unused `CATEGORY_MAP` dict from builder
- Code cleanup — remove unused imports, verify ruff linting passes

#### Fixed

- Run full test suite, performance benchmarks, and quickstart validation scenarios

### [022-measurement-engine-token-points](specs/022-measurement-engine-token-points) Token Points Measurement Engine — estimates AI computational cost from CFM and CSM

#### Added

- Create `specmetrics/plugins/measurement/token_points/` and `specmetrics/plugins/calibration/` packages
- Create measurement models (`TokenPointsMeasurement`, `SpecificationCost`, `CodeGenerationCost`, `TokenContribution`, `MeasurementMetadata`, `MeasurementWarning`)
- Create calibration models (`CalibrationProfile`, `SpecificationCostWeights`, `CodeGenerationCostWeights`) with defaults and YAML loader/validator
- Create core calculator — `calculate(cfm, csm, calibration)` with O(n) single-pass iteration
- Create explainer — ranked contribution list, top contributors, measurement breakdown
- Create `TokenPointsPlugin`, `TokenPointsHandler`, `create_token_points_measurement_metadata`
- Register entry point in `pyproject.toml`
- Implement `top_contributors` method and `aggregate(measurements)` helper
- Add `EventType.TOKEN_POINTS_MEASURED` and emit event from handler
- Track `cfm.unclassified` and `csm.references` element counts in metadata
- Add unit, contract, and integration tests for all phases

#### Fixed

- Run full test suite, performance benchmarks (SC-006: 500 elements in under 2s), and quickstart validation scenarios

### [023-measurement-engine-cognitive-points](specs/023-measurement-engine-cognitive-points) Cognitive Points Measurement Engine — estimates human cognitive effort using Bloom taxonomy and Fibonacci normalization

#### Added

- Create `specmetrics/plugins/measurement/cognitive_points/` package and test directories
- Create measurement models (`CognitivePointsMeasurement`, `SpecificationReviewEffort`, `FunctionalValidationEffort`, `CognitiveContribution`, `FibonacciNormalizationResult`, `MeasurementMetadata`, `MeasurementWarning`)
- Create Bloom classifier with default element-type-to-level mapping
- Create Fibonacci normalizer with configurable threshold table and default scale (1, 3, 5, 8, 13, 20, 40, 100)
- Create `CognitiveCalibrationProfile`, `BloomClassification`, `FibonacciNormalizationProfile` models with YAML loader
- Create core three-stage calculator — Bloom classify, weight sum per component, Fibonacci normalize
- Create explainer — ranked contribution list, bloom_breakdown per component, top contributors
- Create `CognitivePointsPlugin`, `CognitivePointsHandler`, `create_cognitive_points_measurement_metadata`
- Register Cognitive Points entry point in `pyproject.toml`
- Implement `top_contributors`, `bloom_breakdown`, and `aggregate(measurements)` helper
- Add unit, contract, and integration tests for all phases

#### Changed

- Fix `_resolve_calibration` in plugin.py — use `isinstance` guard matching Token Points handler pattern

#### Fixed

- Run full test suite, performance benchmarks (SC-006: 500 elements in under 2s), and quickstart validation scenarios

### [024-measurement-engine-storypoints](specs/024-measurement-engine-storypoints) Story Points Measurement Engine — estimates relative implementation effort via multi-factor weighted sum and Modified Fibonacci normalization

#### Added

- Create `specmetrics/plugins/measurement/storypoints/` package and test directories
- Create measurement models (`StoryPointMeasurementResult`, `FunctionalWorkItem`, `RawEffortScore`, `StoryPointEstimate`, `MeasurementEvidence`, `ExecutionMetadata`, `MeasurementWarning`, `EvidenceRef`)
- Create factor scorer with default scoring rules for all 6 factors (business_interactions, logical_information, external_integrations, business_rule_density, workflow_breadth, exception_handling)
- Create Fibonacci normalizer with configurable threshold table and default scale (1, 2, 3, 5, 8, 13, 20, 40, 100)
- Create core calculator — SHA-256 fingerprint dedup, multi-factor scoring, coefficient application, normalization
- Create explainer — per-item factor_breakdown, evidence_refs, top-contributor ranking
- Create `StoryPointsPlugin`, `StoryPointsHandler`, `create_storypoints_measurement_metadata`
- Register Story Points entry point in `pyproject.toml`
- Implement Rule Pack override integration — coefficient/threshold overrides from CFM metadata annotations
- Implement OpenTelemetry metrics — duration histogram, estimated items gauge, distribution histogram
- Implement incremental execution — carry forward unmodified items with cached estimates
- Add unit, contract, and integration tests for all phases

#### Fixed

- Run full test suite, performance benchmarks (SC-003: 500 FPs in under 5s), and quickstart validation scenarios

### [025-measurement-engine-tshirt](specs/025-measurement-engine-tshirt) T-Shirt Sizing — classifies Story Points into relative effort categories (XS–XXL)

#### Added

- Create `specmetrics/plugins/measurement/tshirt/` package
- Add `TSHIRT_CLASSIFICATION_COMPLETED` to `EventType` enum and to `CANONICAL_EVENT_ORDER`
- Create measurement models (`TShirtMeasurementResult`, `FunctionalWorkItem`, `TShirtSize`, `MeasurementEvidence`, `ExecutionMetadata`, `MeasurementWarning`)
- Create classifier with default mapping table and validation rules (overlap rejection, non-empty ranges)
- Create explainer — per-item evidence_refs, distribution aggregation, mapping_rule traceability
- Create `TShirtPlugin`, `TShirtHandler`, `create_tshirt_measurement_metadata`
- Register T-Shirt entry point in `pyproject.toml`
- Implement Rule Pack override integration in classifier
- Implement OpenTelemetry metrics — classification duration histogram, classified items gauge, distribution histogram
- Add unit, contract, and integration tests for all phases

#### Fixed

- Run full test suite, performance benchmarks (SC-003: 500 FPs in under 1s), and quickstart validation scenarios

### [026-measurement-engine-bcp](specs/026-measurement-engine-bcp) Business Complexity Points — adapter between SpecMetrics and external `bcp-calculator` SDK

#### Added

- Create `specmetrics/plugins/measurement/bcp/` package and test directories
- Create measurement models (`BCPMeasurementResult`, `BCPWorkItem`, `GeneratedStory`, `SDKResult`, `MeasurementEvidence`, `ExecutionMetadata`, `MeasurementWarning`)
- Create story generator — `generate_story(fp, cfm)` converts FunctionalProcess into markdown user story
- Create SDK adapter — `BcpSdkAdapter` wrapping `BCPClient` with dual import path, exponential backoff retry (3 attempts: 1s, 2s, 4s), error translation
- Create explainer — per-item evidence_refs, SDK response preservation, component breakdown
- Create `BCPPlugin`, `BCPHandler`, `create_bcp_measurement_metadata`
- Register BCP entry point in `pyproject.toml`
- Implement provider selection (OpenAI/Claude) and credential validation
- Implement OpenTelemetry metrics — SDK duration histogram, processed story gauge, request/error counters
- Add unit, contract, and integration tests for all phases

#### Fixed

- Run full test suite, quickstart validation scenarios, and code cleanup (ruff)

[Unreleased]: https://github.com/amaurycarvalho/specmetrics/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/amaurycarvalho/specmetrics/releases/tag/v0.3.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
