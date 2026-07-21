# Feature Specification: Token Points Improvements

**Feature Branch**: `038-token-points-improvements`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Levante como é calculado o Token Points. Proponha melhorias para que essa métrica se torne mais realista, aplicável e represente melhor uma estimativa de gasto de tokens relacionadas as especificações speckit ou openspec analisadas pelo specmetrics. O objetivo é conseguir estabelecer um comparativo de gasto de tokens entre as diferentes especificações, visando quebrar especificações para que estas tenham aproximadamente o mesmo nivel de gasto em tokens, e assim viabilizar que métricas de fluxo (ex: throughput, percentis) possam ser melhor aplicadas garantindo um fluxo previsível em um sistema Kanban. Por fim, acrescente uma seção no RFC-028 (docs/rfcs/) descrevendo como o cálculo é feito na prática após as melhorias aplicadas."

## Current State Analysis

The Token Points metric currently calculates a score as:

```
Token Points = Specification Cost + Code Generation Cost
```

Where:
- **Specification Cost** = sum of per-element weights from CSM (Specification Activities, Decisions, Assumptions, Constraints, Risks, Open Questions, Acceptance Criteria, Glossary Terms). Each element type has a flat weight (e.g., decisions=1.5, risks=2.0). References are counted but weighted 0.0. Specification Activities default to 0.0 unless overridden by a YAML calibration file.
- **Code Generation Cost** = sum of per-element weights from CFM (Functional Processes, Business Rules, Operations, Data Groups, Relationships, Actors). Each element type has a flat weight (e.g., functional_processes=5.0, actors=1.0).

**Key limitations identified**:
1. Flat weights ignore element complexity — two functional processes of vastly different scope receive identical scores
2. No content-based estimation — element names and descriptions are not tokenized; the metric counts elements, not content
3. CSM activities default to 0.0, making specification cost artificially low in default configuration
4. No relationship weighting — an operation inside a functional process doesn't increase the process's estimated complexity
5. CSM references are excluded (weighted 0.0) despite representing real specification content
6. Weights are arbitrary floats with no grounding in actual LLM token consumption data
7. No per-sub-type variation within collections (e.g., all BusinessRules receive the same weight regardless of rule_type)
8. Specification and Code costs are treated as independent sums with no ratio modeling

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Content-Based Token Estimation (Priority: P1)

As a project manager comparing specifications across different teams, I want Token Points to estimate actual token consumption based on the content of specification elements (their names, descriptions, and text bodies), not just a flat count of elements. This makes the metric grounded in reality and comparable between different specification formats (SpecKit and OpenSpec).

**Why this priority**: Content-based estimation is the foundation for all other improvements. Without it, the metric remains an arbitrary element counter that cannot be used for cross-project comparison or Kanban flow sizing.

**Independent Test**: Run Token Points on two specifications — one with a functional process containing a 1000-word description, another with a functional process containing a 10-word description. Verify the first scores significantly higher than the second, proportional to the content volume difference.

**Acceptance Scenarios**:

1. **Given** a specification with 3 functional processes of varying description lengths (50, 200, and 800 words), **When** Token Points is calculated, **Then** the score for each process is proportional to its content volume, not a flat 5.0 for each.

2. **Given** the same specification analyzed through SpecKit and OpenSpec adapters, **When** Token Points is calculated for both, **Then** the resulting scores differ by less than 10% because both are content-based, not structure-based.

3. **Given** a specification element with only a name and no description, **When** Token Points is calculated, **Then** the element receives a baseline weight based on its type, plus a token count derived from the name text.

---

### User Story 2 - Cross-Specification Comparability (Priority: P1)

As a Kanban flow manager, I want Token Points values to be comparable across different specification files and projects, so I can identify which specifications are larger (in token terms) and decide how to split them into work items of roughly equal token cost.

**Why this priority**: Comparability enables the Kanban use case — uniform work item sizing for predictable flow. This is the primary business goal stated in the feature description.

**Independent Test**: Generate Token Points for 5 different specification files. Verify that the resulting scores form a meaningful distribution (ratio between largest and smallest is less than 20:1 for specifications of similar functional scope). Verify that specifications with 2x more content volume score approximately 2x higher.

**Acceptance Scenarios**:

1. **Given** a large specification with Token Points score of 5000, **When** the specification is manually split into two halves of roughly equal content, **Then** each half scores approximately 2500 (±15%) Token Points.

2. **Given** two specifications of different sizes in the same project, **When** comparing their Token Points scores, **Then** the ratio between them reflects the actual content volume ratio (e.g., a spec with 2x more text scores approximately 2x higher).

3. **Given** a project with 10 specification files, **When** Token Points is calculated for each, **Then** the scores can be used to group specifications into size buckets (e.g., S: <500, M: 500-1500, L: >1500) as a conceptual usage pattern for Kanban work item sizing — this grouping is a manual or external practice driven by the metric values, not an automated software feature.

---

### User Story 3 - Updated Calibration Profile with Activity Defaults (Priority: P2)

As a platform administrator, I want the default calibration profile to include reasonable weights for Specification Activities (exploration, clarification, refinement, review, validation), so that the specification cost is meaningful out-of-the-box without requiring a custom YAML calibration file.

**Why this priority**: The current default of 0.0 for all activities makes the metric misleading for new users. Sensible defaults improve adoption and reduce configuration burden.

**Independent Test**: Run Token Points on a specification with specification activities present. Verify that Specification Cost > 0 even without a custom calibration file. Verify that different activity types receive different weights reflecting their relative token cost.

**Acceptance Scenarios**:

1. **Given** a specification with a "review" activity and a "validation" activity, **When** Token Points is calculated with default calibration, **Then** review receives a lower weight than validation (reflecting that review is less token-intensive than validation).

2. **Given** no custom calibration file is present, **When** Token Points is calculated, **Then** Specification Activities contribute a positive amount to the total (not 0.0), using sensible default weights for each activity type.

3. **Given** a custom calibration YAML file overrides activity weights, **When** Token Points is calculated, **Then** the custom weights take priority over the new defaults.

---

### User Story 4 - RFC-028 Documentation Update (Priority: P2)

As a developer or user reading the RFC documentation, I want RFC-028 to include a section describing the improved calculation methodology with content-based estimation, so the documentation accurately reflects the implemented behavior.

**Why this priority**: Documentation must match implementation. The RFC is the authoritative reference for how Token Points works.

**Independent Test**: Open `docs/rfcs/RFC-028 - Token Points Measurement Engine.md` and verify it contains a section titled "Content-Based Estimation (v2)" or equivalent, describing the token counting approach, content-based weighting formula, and how it differs from the original flat-weight approach.

**Acceptance Scenarios**:

1. **Given** RFC-028 is opened, **When** reading the new section, **Then** it explains how element content (name, description, body text) is tokenized and factored into the score.

2. **Given** RFC-028 is opened, **When** reading the new section, **Then** it documents the updated calibration profile with default activity weights.

3. **Given** RFC-028 is opened, **When** reading the new section, **Then** it explains how the content-based approach enables cross-specification comparability and provides usage recommendations for Kanban work item sizing using Token Points values as a grouping heuristic.

---

### Edge Cases

- What happens when an element has zero-length content (empty name and description)?
  - The element receives only the baseline type-based weight (no content bonus). It is still counted because its presence in the specification is significant.

- What happens when specification text contains non-natural-language content (code blocks, tables, diagrams)?
  - Code blocks and tables within descriptions are tokenized as text (they represent real content that would consume tokens). Diagram references (image links) are counted as a small fixed token estimate.

- What happens when the same specification is analyzed with different tokenizers (different LLM models)?
  - The metric uses a standard tokenizer (e.g., GPT-4 tokenizer via tiktoken) for consistency. Token Points is a functional size metric, not a billing estimator — model-specific token differences are out of scope.

- What happens with extremely large specifications (10,000+ elements)?
  - The algorithm scales linearly. Performance target remains the same as the current implementation.

- What happens when calibration weights are set to negative values?
  - Validation rejects negative weights. All weights must be >= 0.

## Constitution Check *(mandatory)*

**Engaged Principles**:

- **IV - LLM-Assisted, Deterministic Results**: Token Points remains a deterministic measurement engine. Content-based estimation uses token counting (deterministic) and configurable weights (deterministic). No LLM is used in the calculation itself.
- **V - Evidence First**: Content-based scores are grounded in actual specification text. Each entity's content token count is evidence for its score.
- **VI - Explainability by Design**: The improved calculation is more explainable — the score for each element is a sum of its type weight + its content token count. Users can understand both components.
- **VII - Canonical Representation**: Changes operate on CSM and CFM, preserving canonical isolation. Framework-specific content is already normalized before reaching the engine.
- **IX - Rule Externalization**: Calibration weights remain in external YAML profiles. Content token counting uses a fixed tokenizer (not configurable), but the type-based weights are fully externalizable.
- **XIII - Evolution Without Disruption**: The improved calculation produces different absolute values than the current flat-weight approach, but this is expected — the metric was marked as needing calibration. Old calibration files with flat weights can still be used; content-based estimation is additive.

**Compliance Notes**: The feature changes how per-element scores are computed (adding content-based estimation alongside type-based weights) but preserves the existing calibration profile architecture, plugin interface, and deterministic guarantees. No changes to the CSM, CFM, or extraction pipeline are required.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Token Points engine MUST estimate token consumption based on the content (name, description, and body text) of each specification element, in addition to its element type weight.
- **FR-002**: The content-based estimation MUST use a deterministic tokenizer (e.g., cl100k_base for GPT-4 compatible counting) to count tokens in element text content.
- **FR-003**: Each element's partial score MUST be computed as: `score = type_weight + (content_token_count × content_multiplier)`, where `content_multiplier` is a configurable calibration parameter (default: 0.1).
- **FR-004**: The default calibration profile MUST include non-zero weights for all five Specification Activity types: exploration (2.0), clarification (3.0), refinement (3.0), review (1.5), validation (2.0).
- **FR-005**: CSM references MUST receive a positive weight (default: 1.0) in the default calibration profile, reflecting their contribution to specification complexity.
- **FR-006**: The per-element content token count MUST be logged as part of each `TokenContribution`'s metadata, enabling auditing of the content-based portion of the score.
- **FR-007**: The existing `token_element_counts` payload key MUST be extended to include content token counts per element type (not just element counts).
- **FR-008**: The existing calibration YAML format MUST remain backward-compatible — loading an old profile without content_multiplier or activity weights MUST fall back to the new defaults (not 0.0).
- **FR-009**: RFC-028 (`docs/rfcs/RFC-028 - Token Points Measurement Engine.md`) MUST be updated with a new section documenting the content-based estimation methodology, updated calibration defaults, and usage recommendations including how the metric enables specification sizing for Kanban flow (e.g., grouping specifications into similar Token Points buckets for uniform work items).

### Key Entities

- **TokenContribution** (updated): Now includes `content_token_count` (int) and `content_score` (float) alongside the existing `partial_score` (which becomes `type_score + content_score`).
- **ContentEstimationConfig**: New calibration sub-configuration with `content_multiplier` (default 0.1), controlling how much content token count contributes to the total score relative to type weight.
- **CalibrationProfile** (updated): `SpecificationCostWeights.activities` now defaults to the five non-zero values. Added `content_multiplier` field. Added `references` weight.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For two specifications whose content volume ratio is 2:1 (measured in character count), the Token Points ratio is between 1.5:1 and 2.5:1 (i.e., the metric correlates with content volume, not just element count).
- **SC-002**: Running Token Points with the default calibration (no custom YAML) on a specification containing specification activities produces a Specification Cost > 0.
- **SC-003**: The `token_element_counts` payload includes a new field per element type: `content_tokens` (total token count of all elements of that type's text content).
- **SC-004**: RFC-028 contains at least one new section (minimum 200 words) describing the content-based estimation methodology, updated defaults, and usage recommendations for Kanban flow sizing.

## Clarifications

### Session 2026-07-21

- Q: Specification chunking (FR-009) — is it a feature to implement? → A: No. Chunking is a conceptual use case for how the metric can be applied in Kanban workflows, not a software feature to build or expose via CLI.

## Assumptions

- The `tiktoken` library (or equivalent) is available for token counting. If not installed, the engine falls back to character-count-based estimation (4 chars ≈ 1 token).
- The `content_multiplier` value of 0.1 means that 100 tokens of element text add 10.0 to the score — keeping content contribution at a similar order of magnitude as type weights (1.0 to 5.0).
- Existing calibration YAML files that set activity weights explicitly will continue to work — the new defaults only apply when no explicit weights are configured.
- The tokenizer model (cl100k_base) is the GPT-4/OpenAI standard tokenizer. If other tokenizers are needed in the future, they can be added as calibration options without changing the calculation formula.
- The content_multiplier can be overridden in calibration YAML, allowing organizations to tune the balance between type-based and content-based scoring.
