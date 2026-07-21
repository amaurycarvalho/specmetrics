# Feature Specification: Cognitive Points Improvements

**Feature Branch**: `039-cognitive-points-improvements`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Levante como é calculado o Cognitive Points. Proponha melhorias para que essa métrica se torne mais realista, aplicável e represente melhor uma estimativa do esforço humano cognitivo relacionadas as especificações speckit ou openspec analisadas pelo specmetrics. O objetivo é conseguir estabelecer um comparativo de esforço cognitivo entre as diferentes especificações, visando que com essa informação disponivel o usuario possa posteriormente quebrar manualmente suas especificações para que estas tenham aproximadamente o mesmo nivel de esforço cognitivo, e assim viabilizar que métricas de fluxo (ex: throughput, percentis) possam ser melhor aplicadas garantindo um fluxo previsível em um sistema Kanban. Esse ato de quebrar especificações para terem o mesmo tamanho é apenas uma prática metodologica do Kanban, sem que o specmetrics tenha qualquer funcionalidade especifica para tal. Por fim, acrescente uma seção no RFC-029 (docs/rfcs/) descrevendo como o cálculo é feito na prática após as melhorias aplicadas."

## Current State Analysis

The Cognitive Points metric estimates human cognitive effort by classifying each specification element into a Bloom taxonomy level and summing the associated weights:

```
Raw Score = sum of Bloom weights across all CSM and CFM elements
Cognitive Points = Fibonacci_Normalize(raw_score)
```

Where:
- **Bloom taxonomy** has 6 levels with weights: remember (1.0), understand (2.0), apply (3.0), analyze (4.0), evaluate (5.0), create (8.0).
- **Element classification** uses a fixed mapping: functional_process → create (8.0), business_rule → apply (3.0), decision → evaluate (5.0), glossary_term → remember (1.0), etc. (18 element types mapped, unknown types default to analyze/4.0).
- **Fibonacci normalization** maps raw_score through 7 thresholds to output values 1, 3, 5, 8, 13, 20, 40, 100.
- **Two effort components**: Specification Review Effort (CSM elements) and Functional Validation Effort (CFM elements).

**Key limitations identified**:
1. Flat Bloom weights per element — a functional process with 5-word description scores identically to one with 500-word description (both = 8.0)
2. No content-based estimation — only element type matters, not the cognitive depth of the content
3. Hard Fibonacci ceiling at 100 — large specifications hit the ceiling and lose differentiation
4. Single Bloom level per element type — all functional processes are "create" regardless of whether they describe a simple CRUD or complex business workflow
5. Default fallback at "analyze" (4.0) is too aggressive for unknown element types
6. No cross-element cognitive relationships — a process with 10 operations has the same score as one with 2 (since each element is independently classified)
7. Element name truncation at 80 characters loses content without warning

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Content-Based Cognitive Scoring (Priority: P1)

As a project manager comparing the cognitive complexity of different specifications, I want Cognitive Points to reflect not just what type each element is but also how cognitively dense its content is. A functional process with an elaborate description should score higher than one with a trivial description, because it demands more human cognitive effort to understand.

**Why this priority**: Content-based scoring is the foundation for cross-specification comparability. Without it, the metric is a simple element counter weighted by Bloom taxonomy — useful but not proportional to actual cognitive effort.

**Independent Test**: Run Cognitive Points on two specifications — one with functional processes containing detailed descriptions (100+ words each), another with the same number of functional processes containing only titles. Verify the first scores significantly higher than the second.

**Acceptance Scenarios**:

1. **Given** two specifications with identical element types and counts but one has 3x more descriptive content (measured in tokens), **When** Cognitive Points is calculated for both, **Then** the content-richer specification scores between 1.5x and 3.5x higher than the content-sparse one.

2. **Given** a functional process with a 500-token description, **When** Cognitive Points is calculated, **Then** the element's contribution includes both its Bloom weight (8.0 for "create") and a content-based component proportional to its description length.

3. **Given** a specification element with only a name and no description, **When** Cognitive Points is calculated, **Then** the element receives its Bloom weight plus a small content component from the name text only.

---

### User Story 2 - Cross-Specification Cognitive Comparability (Priority: P1)

As a Kanban flow manager, I want Cognitive Points values to be comparable across different specification files and projects, so I can compare the relative cognitive effort of different work items and manually organize specifications into similarly-sized groups for predictable flow.

**Why this priority**: Comparability enables the Kanban use case — uniform work item sizing for predictable flow. This is the primary business goal. The breaking of specifications into equal chunks is a manual Kanban practice, not a specmetrics feature.

**Independent Test**: Generate Cognitive Points for 5 specification files with known content volumes. Verify that the ratio between scores correlates with the ratio between content volumes. Verify that two specifications with similar element counts and similar content volumes produce Cognitive Points within 20% of each other.

**Acceptance Scenarios**:

1. **Given** two specifications where one has 2x the total content volume of the other (measured in tokens), **When** Cognitive Points is calculated, **Then** the ratio between their raw scores is between 1.3:1 and 3.0:1 (Bloom weights introduce some non-linearity, but content should drive the majority of the difference).

2. **Given** specifications from two different SDD frameworks (SpecKit and OpenSpec), **When** Cognitive Points is calculated for both, **Then** the scores differ by less than 15% if the two specifications have similar content volume, because the metric is content-based and framework-agnostic.

3. **Given** 10 specification files from a project, **When** Cognitive Points is calculated, **Then** the raw scores can be compared directly to identify which specifications are cognitively "larger" and which are "smaller," enabling manual grouping decisions.

---

### User Story 3 - Granular Bloom Classification with Sub-Types (Priority: P2)

As a specification author, I want Cognitive Points to differentiate between sub-types within the same element category, so that a "policy" business rule (constraint-oriented) receives a different cognitive weight than a "derivation" business rule (computation-oriented). Sub-types that require higher-order thinking should map to higher Bloom levels.

**Why this priority**: Sub-type classification adds granularity to the Bloom mapping without adding complexity to the scoring formula. It makes the base (non-content) component more accurate before content-based estimation is applied.

**Independent Test**: Run Cognitive Points on a specification containing BusinessRules of different sub-types (constraint, condition, policy, derivation). Verify they are classified into appropriate Bloom levels (not all "apply").

**Acceptance Scenarios**:

1. **Given** a BusinessRule with `rule_type: "derivation"` (involving computation), **When** classified by the Bloom classifier, **Then** it maps to a higher Bloom level (e.g., "analyze" or "evaluate") than a `rule_type: "constraint"` BusinessRule (which maps to "apply").

2. **Given** an Operation with specific operation type metadata (e.g., CRUD read vs. complex transaction), **When** classified, **Then** simple operations map to "apply" while complex operations map to "analyze" or higher.

3. **Given** an element type not in the Bloom mappings with no sub-type information, **When** classified, **Then** it falls back to a more conservative default (e.g., "understand"/2.0 instead of the current "analyze"/4.0).

---

### User Story 4 - RFC-029 Documentation Update (Priority: P2)

As a developer or user reading the RFC documentation, I want RFC-029 to include a section describing the improved calculation methodology with content-based estimation and sub-type classification, so the documentation accurately reflects the implemented behavior.

**Why this priority**: Documentation must match implementation. The RFC is the authoritative reference for how Cognitive Points works.

**Independent Test**: Open `docs/rfcs/RFC-029 - Cognitive Points Measurement Engine.md` and verify it contains a section titled "Content-Based Estimation (v2)" or equivalent, describing the improved methodology.

**Acceptance Scenarios**:

1. **Given** RFC-029 is opened, **When** reading the new section, **Then** it explains the content-based scoring formula and how it complements Bloom taxonomy classification.

2. **Given** RFC-029 is opened, **When** reading the new section, **Then** it documents the updated Bloom mappings with sub-type differentiation.

3. **Given** RFC-029 is opened, **When** reading the new section, **Then** it explains how the content-based approach enables cross-specification cognitive comparability and provides usage recommendations for Kanban work item sizing as a conceptual practice.

---

### Edge Cases

- What happens when an element has zero-length content (empty name and description)?
  - The element receives only its Bloom weight (no content component). The content_token_count is 0 and content_score is 0.0.

- What happens when specification text contains code blocks or tables?
  - Code blocks and tables within descriptions are tokenized as text — they represent cognitive content that a human must understand.

- What happens when the content_multiplier is set to 0.0 (disabled)?
  - The engine reverts to pure Bloom taxonomy scoring, identical to the pre-improvement behavior. This is the backward-compatibility path.

- What happens when an element has sub-type metadata but the sub-type is not in the Bloom mappings?
  - The classifier falls back to the element's base type mapping, and if that is also absent, to the default Bloom level. A warning is logged for unrecognized sub-types.

- What happens with extremely large specifications (raw score > 200,000)?
  - The Fibonacci normalizer may hit its ceiling (last output value). The raw score is always preserved and available for comparison. The ceiling value can be configured via calibration.

## Constitution Check *(mandatory)*

**Engaged Principles**:

- **IV - LLM-Assisted, Deterministic Results**: Cognitive Points remains deterministic. Content token counting and Bloom classification are both fully deterministic algorithms.
- **V - Evidence First**: Content token counts are evidence for the content-based portion of the score. Bloom classifications reference element type and sub-type metadata.
- **VI - Explainability by Design**: The improved formula `bloom_weight + (content_tokens × content_multiplier)` is transparent. Users can see both the Bloom contribution and the content contribution.
- **VII - Canonical Representation**: Operates on CSM and CFM. Framework-specific content is already normalized.
- **IX - Rule Externalization**: Bloom mappings, Bloom weights, content_multiplier, and Fibonacci thresholds are all in external calibration profiles.
- **XIII - Evolution Without Disruption**: Old calibration files without content_multiplier or sub-type mappings continue to work (defaults fill in). Scores change meaningfully (intentional improvement).

**Compliance Notes**: The feature adds content-based estimation to an already-deterministic engine. No changes to the CSM, CFM, or extraction pipeline. The Bloom classification algorithm's core contract (classify element → return bloom level) is preserved; the enhancement adds sub-type awareness.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Cognitive Points engine MUST estimate cognitive effort based on the content (name and description text) of each specification element, in addition to its Bloom taxonomy classification.
- **FR-002**: The content-based estimation MUST use a deterministic tokenizer to count tokens in element text content, with the same tokenizer and fallback strategy used by the Token Points engine.
- **FR-003**: Each element's partial score MUST be computed as: `score = bloom_weight + (content_token_count × content_multiplier)`, where `content_multiplier` is a configurable calibration parameter (default: 0.1).
- **FR-004**: The per-element `content_token_count` and `content_score` MUST be recorded in each `CognitiveContribution`'s metadata, alongside the existing `cognitive_weight` and `partial_score`.
- **FR-005**: The Bloom classifier MUST support sub-type classification: when an element has sub-type metadata (e.g., `rule_type`, `operation_type`, `activity_type`), the classifier MUST look up the sub-type in the Bloom mappings before falling back to the base element type or default.
- **FR-006**: The default Bloom mapping MUST include sub-type entries for BusinessRules (constraint → apply/3.0, condition → analyze/4.0, policy → evaluate/5.0, derivation → evaluate/5.0) and Operations (standard → apply/3.0, conditional → analyze/4.0, iterative → analyze/4.0, transactional → create/8.0).
- **FR-007**: The default Bloom level for unknown element types MUST be changed from "analyze" (4.0) to "understand" (2.0) to be more conservative.
- **FR-008**: The existing payload keys MUST be extended: `cognitive_content_multiplier`, `cognitive_content_tokens` (per element type totals), and `content_tokens` field in each entry of `cognitive_element_counts`.
- **FR-009**: The existing calibration profile format MUST remain backward-compatible — loading an old profile without `content_multiplier` or sub-type mappings MUST fall back to the new defaults.
- **FR-010**: RFC-029 (`docs/rfcs/RFC-029 - Cognitive Points Measurement Engine.md`) MUST be updated with a new section documenting the content-based estimation methodology, updated Bloom mappings with sub-type classification, and usage recommendations for cross-specification cognitive comparability and Kanban flow sizing as a conceptual practice.

### Key Entities

- **CognitiveContribution** (updated): Now includes `content_token_count` (int) and `content_score` (float) alongside the existing `cognitive_weight`, `bloom_level`, and `partial_score` (which becomes `cognitive_weight + content_score`).
- **ContentEstimationConfig**: Calibration sub-configuration with `content_multiplier` (default 0.1), shared with the Token Points engine's configuration pattern.
- **BloomMapping** (updated): Now supports sub-type keys in the format `base_type.sub_type` (e.g., `"business_rule.constraint"` → apply, `"business_rule.derivation"` → evaluate). Lookup order: `base_type.sub_type` → `base_type` → `default_bloom_level`.
- **CognitiveCalibrationProfile** (updated): Added `content_multiplier` field (default 0.1). Updated `bloom_mappings` with sub-type entries. Changed `default_bloom_level` from "analyze" to "understand".

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For two specifications with identical element types and counts but one having 3x the content volume, the content-richer specification's raw score is at least 1.5x higher than the content-sparse one.
- **SC-002**: Two specifications from different SDD frameworks (SpecKit and OpenSpec) with similar content volumes produce Cognitive Points raw scores within 15% of each other.
- **SC-003**: A BusinessRule with `rule_type: "derivation"` is classified into a higher Bloom level (≥ "analyze") than a BusinessRule with `rule_type: "constraint"` (Blom level "apply").
- **SC-004**: An unknown element type (not in mappings) defaults to Bloom level "understand" (weight 2.0) instead of "analyze" (weight 4.0).
- **SC-005**: The `cognitive_content_tokens` and `cognitive_content_multiplier` keys appear in the measurement payload output.
- **SC-006**: RFC-029 contains at least one new section (minimum 200 words) describing the content-based methodology, sub-type classification, and Kanban usage recommendations.

## Assumptions

- The content tokenization infrastructure (tokenizer + fallback) developed for Token Points improvements (spec 038) is reused. Cognitive Points calls the same `count_tokens()` function.
- The `content_multiplier` default of 0.1 is consistent with Token Points — 100 tokens of content add 10.0 to the score, comparable to Bloom weights (1.0 to 8.0).
- Specification breaking into equal cognitive chunks is a manual Kanban practice. The Cognitive Points metric provides the comparability data that enables this practice, but specmetrics does not implement automatic chunking.
- Sub-type metadata (rule_type, operation_type, etc.) is available on CSM/CFM elements after semantic extraction. If absent, the base-type mapping is used.
- Existing calibration YAML files without `content_multiplier` or sub-type mappings load with the new defaults via Pydantic field defaults.
- Bloom weights (1.0 through 8.0) remain unchanged — they are well-established in cognitive science literature and do not need calibration adjustment in this feature.
