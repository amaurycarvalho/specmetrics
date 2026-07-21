# Feature Specification: Story Points Improvements

**Feature Branch**: `040-story-points-improvements`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Levante como e calculado o Story Points. Proponha melhorias para que essa metrica se torne mais realista, aplicavel e represente melhor a estimativa de esforco de implementacao relacionada as especificacoes speckit ou openspec analisadas pelo specmetrics. O objetivo e conseguir estabelecer um comparativo de esforco de implementacao entre as diferentes especificacoes, visando que com essa informacao disponivel o usuario possa posteriormente quebrar manualmente suas especificacoes para que estas tenham aproximadamente o mesmo nivel de esforco, e assim viabilizar que metricas de fluxo (ex: throughput, percentis) possam ser melhor aplicadas garantindo um fluxo previsivel em um sistema Kanban. Esse ato de quebrar especificacoes para terem o mesmo tamanho e apenas uma pratica metodologica do Kanban, sem que o specmetrics tenha qualquer funcionalidade especifica para tal."

## Clarifications

### Session 2026-07-21

- Q: Should normalization recalibrate thresholds for content-augmented scores? → A: Story Points is a relative scoring system. All raw scores across entities within a specification are sorted in ascending order, then mapped to the Modified Fibonacci scale (1, 2, 3, 5, 8, 13, 20, 40, 100) so that lower raw scores map to lower Fibonacci values and higher raw scores map to higher Fibonacci values. There are no fixed raw-score thresholds — the distribution is determined by the relative ranking of entities within the specification.

## Current State Analysis

### How Story Points Are Currently Calculated

The Story Points measurement engine estimates relative implementation effort using a multi-factor weighted sum approach applied exclusively to Functional Processes from the Canonical Functional Model (CFM).

**Algorithm (per Functional Process)**:

```
raw_score = SUM over 6 factors of ( factor_raw_count * factor_coefficient )
```

**The six structural factors**:

| Factor | What It Measures | Default Weight |
|---|---|---|
| Business Interactions | Number of actors associated with the functional process | 1.0 |
| Logical Information | Number of data groups + operations linked to the process | 1.0 |
| External Integrations | Number of "communicates_with" relationships involving the process | 2.0 |
| Business Rule Density | Number of business rules referencing the process | 1.5 |
| Workflow Breadth | Number of operations whose parent is the functional process | 1.0 |
| Exception Handling | Whether any operation has conditional/branching/exception type (binary) | 3.0 |

**Normalization**: Raw scores are mapped to a Modified Fibonacci scale (1, 2, 3, 5, 8, 13, 20, 40, 100) using fixed thresholds by default (e.g., raw < 2 → 1, 2-4 → 2, ..., > 85 → 100). This absolute bucket-based mapping will be replaced by relative ranking in the improvements.

**Current limitations**:

1. **CFM-only scope**: Story Points processes only Functional Processes. The entire Canonical Specification Model (CSM) — containing activities (exploration, clarification, refinement, review, validation), decisions, assumptions, constraints, risks, acceptance criteria, and glossary terms — is excluded. Non-process CFM elements (actors, business rules, operations, data groups, relationships) are also excluded individually, only contributing indirectly through their associations with functional processes. Together, these excluded artifacts represent significant specification effort that requires implementation work.

2. **No content-based estimation**: Two functional processes with identical structural characteristics (same actor count, same number of operations, same number of business rules) receive identical Story Points regardless of whether their descriptions are 10 words or 1000 words. Description depth and detail are strong proxies for implementation complexity, yet they are entirely ignored.

3. **No cross-specification comparability**: The metric is scoped to a single specification's functional processes. There is no mechanism to compare the relative implementation effort of different specification files. Users cannot answer the question "is specification A roughly the same size as specification B in terms of implementation effort?"

4. **Invisible calibration context**: The output payload does not expose the calibration parameters (coefficients) that produced a given score. Different runs with different calibrations produce different scores, but the consumer of the output has no way to know why.

## Proposed Improvements

### 1. Content-Based Estimation for All Elements

Add a content dimension to the estimation formula. Every element's score gains a component proportional to the token count of its textual content (name + description):

```
full_score = structural_score + (content_tokens * content_multiplier)
```

For functional processes, the structural score is the existing 6-factor weighted sum. For all other element types, the structural score is a base weight (see Improvement 2).

The content multiplier is a configurable calibration parameter (default value: 0.1), allowing organizations to tune how much textual depth influences the estimate. Setting it to 0.0 disables content-based estimation, producing the exact same results as the current engine.

This preserves full backward compatibility while enabling estimation that reflects actual specification depth.

### 2. Expand Estimation Scope to All Specification Elements

Extend Story Points beyond functional processes to cover every element type present in the canonical models:

**CSM elements** (represent specification effort):

| Element Type | Base Weight | Rationale |
|---|---|---|
| Exploration activities | 4.0 | Research and discovery require significant effort |
| Clarification activities | 5.0 | Resolving ambiguity is high-effort specification work |
| Refinement activities | 5.0 | Iterative improvement demands sustained attention |
| Review activities | 3.0 | Quality assurance through review |
| Validation activities | 3.0 | Verification against requirements |
| Decisions | 5.0 | Architectural decisions carry implementation weight |
| Assumptions | 2.0 | Documented assumptions guide implementation choices |
| Constraints | 3.0 | Constraints shape and limit implementation |
| Risks | 4.0 | Risk mitigation requires implementation investment |
| Open questions | 2.0 | Unresolved questions represent pending effort |
| Acceptance criteria | 3.0 | Each criterion must be implemented and verified |
| Glossary terms | 1.0 | Terminology definition is light but real effort |
| References | 0.5 | Cross-references add minimal implementation burden |

**Non-process CFM elements** (represent implementation building blocks):

| Element Type | Base Weight | Rationale |
|---|---|---|
| Business rules | 4.0 | Rules drive complex validation and enforcement logic |
| Operations | 3.0 | Each operation represents executable behavior |
| Data groups | 3.0 | Data structures require schema, storage, and access logic |
| Relationships | 1.0 | Connections between entities need wiring |
| Actors | 1.0 | Each actor implies interface or integration surface |

Functional processes retain the sophisticated 6-factor weighted sum as their structural score, preserving their richer estimation model.

### 3. Cross-Specification Comparability Payload

Extend the measurement output with fields that enable direct comparison between specifications:

- The content multiplier value used for the run (auditability)
- Per-element-type content token totals (transparency of text volume contribution)
- Separation of specification effort (CSM-derived) from implementation effort (CFM-derived) totals
- Per-element content token count in the detailed breakdown (granular traceability)

Cross-specification comparison uses **raw scores**, which are computed with the same formula regardless of the specification being measured. Normalized Fibonacci values are **within-specification relative rankings** — they answer "which entities are largest within this spec" — not suitable for cross-spec comparison. Raw score totals provide the absolute effort estimate needed to compare two specifications.

With this data, users can compare two specifications' raw scores and determine whether they represent roughly similar implementation effort, or whether one is significantly larger and should be manually decomposed into smaller, similarly-sized work items for Kanban flow.

### 4. Configurable Calibration Parameters

All weights and coefficients become configurable through external calibration profiles:

- Factor coefficients for the 6 structural factors
- Content multiplier value
- Base weights for every element type
- Default fallback weight for unknown element types
- Fibonacci output scale values (default: 1, 2, 3, 5, 8, 13, 20, 40, 100)

Normalization uses relative ranking rather than fixed thresholds: entities are sorted by raw score within the specification and mapped proportionally to the Fibonacci scale. The ranking strategy (how to distribute entities across the 9 Fibonacci buckets) is configurable, with a default of equal-proportion percentile bands.

Old calibration profiles that lack the new parameters load with sensible defaults, preserving backward compatibility.

## User Scenarios & Testing

### User Story 1 - Content-Aware Estimation Reflects Specification Depth (Priority: P1)

As a project manager evaluating specifications, I want Story Points to reflect not just structural characteristics (how many actors, how many rules) but also the depth of each element's written specification. A functional process with a detailed 500-word description should score higher than an identically-structured element with only a title.

**Why this priority**: Content-based estimation is the foundational improvement. Without it, Story Points cannot distinguish between a trivial placeholder and a thoroughly specified feature with identical structure.

**Independent Test**: Create two specifications with identical functional process structure (same actors, operations, business rules, relationships) but one having 3x the description text volume. Verify the content-richer specification produces higher raw scores, and the ratio is proportional to the content multiplier setting.

**Acceptance Scenarios**:

1. **Given** two functional processes with identical structural characteristics but one has 500 description tokens vs. 100 tokens for the other, **When** Story Points is calculated with the default content multiplier, **Then** the content-richer process has a measurably higher raw score, and the difference equals exactly `(500 - 100) * content_multiplier`.

2. **Given** a calibration profile with content multiplier set to 0.0, **When** Story Points is calculated on any specification, **Then** the results match the current factor-only engine exactly (backward compatibility).

3. **Given** a functional process whose name and description are both empty, **When** Story Points is calculated, **Then** the content contribution is zero but the structural factor scores still apply normally.

---

### User Story 2 - Complete Specification Scope Estimation (Priority: P1)

As a team lead, I want Story Points to estimate effort from every element in the specification — not just functional processes — so the total score reflects the full scope of what needs to be implemented and validated. A specification with 50 decisions and 100 acceptance criteria should show significantly higher effort than one with the same functional processes but no supporting artifacts.

**Why this priority**: Functional processes alone cannot represent total implementation effort. Decisions, constraints, business rules, and other artifacts represent real work. Including them makes Story Points a holistic effort metric.

**Independent Test**: Measure a specification containing both CSM elements (decisions, constraints, acceptance criteria) and non-process CFM elements (standalone business rules, data groups). Verify that every element type present in the canonical models contributes to the total score.

**Acceptance Scenarios**:

1. **Given** a specification with 10 decisions, 5 constraints, and 20 acceptance criteria in addition to its functional processes, **When** Story Points is calculated, **Then** the total score includes contributions from all three CSM element types alongside the functional process estimates.

2. **Given** a specification with standalone business rules, operations, data groups, and actors that are not associated with any functional process, **When** Story Points is calculated, **Then** these independent CFM elements contribute to the total score via their base weights.

3. **Given** a specification with only CSM elements and zero functional processes, **When** Story Points is calculated, **Then** a result is still produced from the CSM elements, accompanied by an informational notice that no functional processes were found.

---

### User Story 3 - Cross-Specification Implementation Effort Comparison (Priority: P1)

As a Kanban flow manager, I want Story Points values to be comparable across different specification files and projects, so I can assess whether two specifications represent similar implementation effort and manually organize work items into uniform-sized batches for predictable flow.

**Why this priority**: Cross-specification comparability is the primary business goal. It enables the Kanban practice of uniform work item sizing, which makes flow metrics (throughput, percentiles) meaningful and predictable.

**Independent Test**: Generate Story Points for two specification files with a known 2:1 ratio in total content volume (token count across all elements, both CSM and CFM). Verify the total raw score ratio is meaningfully correlated (between 1.3:1 and 3.0:1), demonstrating that larger specifications consistently score higher.

**Acceptance Scenarios**:

1. **Given** two specifications from the same SDD framework where one has 2x the total description content volume of the other, **When** Story Points is calculated for both, **Then** the larger specification's total raw score is between 1.3x and 3.0x the smaller one's score.

2. **Given** two specifications with similar content volumes but from different SDD frameworks (e.g., one SpecKit, one OpenSpec), **When** Story Points is calculated for both, **Then** the total raw scores differ by less than 15%, demonstrating framework-agnostic estimation.

3. **Given** a Story Points measurement result, **When** the output is inspected, **Then** it contains separate specification effort (CSM-derived) and implementation effort (CFM-derived) totals, enabling the user to understand where the effort comes from.

---

### User Story 4 - Configurable Calibration for Team-Specific Tuning (Priority: P2)

As a team lead, I want the content multiplier, element base weights, factor coefficients, and ranking strategy to be configurable through external calibration profiles, so I can tune Story Points to match my team's historical implementation velocity over time.

**Why this priority**: Configurability enables organizations to calibrate the metric as they gather real-world data. Without it, Story Points remains a one-size-fits-all estimate.

**Independent Test**: Create a calibration profile with a content multiplier of 0.5 and custom base weights. Measure a specification and verify the results reflect the custom parameters. Then measure the same specification with the default calibration and confirm the results differ as expected.

**Acceptance Scenarios**:

1. **Given** a calibration profile with content multiplier set to 0.5 (5x the default), **When** Story Points is calculated on a specification with 1000 content tokens, **Then** the content contribution is 500 (1000 * 0.5), compared to 100 with the default 0.1 multiplier.

2. **Given** a calibration profile that overrides the base weight for decisions from 5.0 to 8.0, **When** Story Points encounters a decision element, **Then** it uses 8.0 as the base weight instead of the default 5.0.

3. **Given** a calibration profile from a previous version that lacks the content multiplier and element base weight fields, **When** loaded, **Then** it falls back to the new defaults (0.1 for content multiplier, standard base weight table) without errors.

4. **Given** a specification containing an element type not listed in the base weight table, **When** Story Points is calculated, **Then** the element uses a configurable default fallback weight and generates an informational notice.

---

### User Story 5 - Documentation of Story Points Methodology (Priority: P2)

As a developer or team lead reading the project documentation, I want a dedicated RFC that fully documents the Story Points measurement engine — including its factors, formulas, normalization logic, element base weights, and cross-specification use cases — so I can understand, trust, and calibrate the metric.

**Why this priority**: Documentation is essential for adoption and trust. Users need to understand the methodology to make informed decisions about calibration and interpretation.

**Independent Test**: Open the Story Points RFC document. Verify it contains sections describing the factor-based weighted sum, content-based estimation formula, element base weight table, Fibonacci normalization, and guidance on using Story Points for cross-specification comparison and Kanban sizing.

**Acceptance Scenarios**:

1. **Given** the Story Points RFC document is opened, **When** reading the estimation methodology section, **Then** it explains the full formula combining structural factors with content tokens.

2. **Given** the RFC document, **When** reading the element coverage section, **Then** it documents every supported element type from both CSM and CFM with their default base weights and rationale.

3. **Given** the RFC document, **When** reading the usage guidance section, **Then** it describes how Story Points enables cross-specification comparability and how users can leverage this data for Kanban work item sizing as a manual practice (no automatic chunking).

---

### Edge Cases

- **Empty name and description**: The content contribution is zero. The structural score (factors or base weight) still applies normally.
- **No CSM elements present**: Story Points estimates from CFM elements only. No notice is needed — this is a valid state for specifications that haven't been through semantic extraction for CSM.
- **No functional processes present**: Story Points estimates from CSM and non-process CFM elements using base weights. An informational notice is emitted.
- **Content multiplier set to 0.0**: Content-based estimation is fully disabled. Functional processes use only the 6 structural factors. Non-FP elements use only their base weights. Results match the current engine output.
- **Code blocks in descriptions**: Code blocks participate in content token counting as regular text — they represent implementation-relevant specification content.
- **Unknown element type in specification**: Uses a configurable default fallback weight. An informational notice is generated identifying the unknown type.
- **Duplicate functional processes** (content-identical): Deduplicated by content fingerprint. Merged duplicates are counted in execution metadata but do not inflate the score.
- **Very large specifications**: The engine processes all elements regardless of count. Performance scales linearly with element count.

## Constitution Check

**Engaged Principles**:

- **IV - LLM-Assisted, Deterministic Results**: All estimation formulas remain fully deterministic — weighted sums of countable quantities (factor counts, token counts). No LLM participates in measurement.
- **V - Evidence First**: Every element contribution preserves references to its source specification text. Content token counts are evidence for the content-based portion of the score. Factor breakdowns are traceable per element.
- **VI - Explainability by Design**: The formula `structural_score + (content_tokens * content_multiplier)` is transparent and auditable. Users can decompose any element's score into its structural and content contributions.
- **VII - Canonical Representation**: The engine operates on the CSM and CFM canonical models exclusively. Framework-specific concepts are already normalized before estimation.
- **VIII - Plugin-Oriented Architecture**: All changes reside within the existing Story Points measurement plugin. No changes to the core platform or other plugins are required.
- **IX - Rule Externalization**: Factor coefficients, element base weights, content multiplier, Fibonacci scale values, and ranking strategy are all externalized in calibration profiles.
- **XIII - Evolution Without Disruption**: Old calibration profiles without the new fields load with sensible defaults. The existing factor-only estimation behavior is preserved when content multiplier is 0.0. Previously generated measurements remain valid.
- **XIV - Layer Independence**: Story Points consumes only the canonical models (CFM and CSM). It does not depend on extraction providers, adapters, or exporters.

**Compliance Notes**: The feature extends the existing multi-factor weighted sum with an additive content-based component. The plugin structure and consumption of canonical models remain unchanged. Normalization changes from fixed-threshold buckets to relative ranking, which better aligns with Story Points as a relative estimation method. The expansion of input scope from CFM-only to CFM+CSM follows the well-established pattern used by Token Points and Cognitive Points.

## Requirements

### Functional Requirements

- **FR-001**: The Story Points engine MUST compute each element's score as `structural_score + (content_tokens * content_multiplier)`, where structural score is the 6-factor weighted sum for functional processes and a base weight for all other element types.

- **FR-002**: Content tokens MUST be counted from the concatenation of each element's name and description text, using the same token counting mechanism shared across all measurement plugins.

- **FR-003**: The content multiplier MUST be a configurable calibration parameter with a default value of 0.1. Setting it to 0.0 MUST produce results identical to the current factor-only engine.

- **FR-004**: The engine MUST estimate contributions from every CSM element type: activities (exploration, clarification, refinement, review, validation), decisions, assumptions, constraints, risks, open questions, acceptance criteria, glossary terms, and references.

- **FR-005**: The engine MUST estimate contributions from every non-process CFM element type: business rules, operations, data groups, relationships, and actors.

- **FR-006**: Each element type MUST have a configurable base weight with the defaults specified in the Proposed Improvements section.

- **FR-007**: Functional processes MUST continue using the 6-factor weighted sum as their structural score, not a flat base weight. The 6 factor coefficients MUST remain configurable.

- **FR-008**: The Fibonacci normalization MUST use relative ranking within the specification: all entity raw scores are sorted in ascending order and mapped proportionally to the Modified Fibonacci scale (1, 2, 3, 5, 8, 13, 20, 40, 100). Lower raw scores map to lower Fibonacci values; higher raw scores map to higher Fibonacci values. This is a relative, not absolute, normalization — there are no fixed raw-score thresholds.

- **FR-009**: Element types not present in the base weight configuration MUST use a configurable default fallback weight and generate an informational notice.

- **FR-010**: The measurement output MUST include: the content multiplier value used for the run, per-element-type content token totals, separate specification effort and implementation effort totals, and per-element content token counts in the detailed breakdown.

- **FR-011**: Calibration profiles from previous versions that lack content multiplier and element base weight fields MUST load successfully with the new defaults applied automatically.

- **FR-012**: A dedicated RFC document MUST be created that fully documents the Story Points measurement methodology, including all formulas, factor definitions, element base weights, normalization logic, calibration parameters, and guidance on cross-specification comparison for Kanban sizing.

- **FR-013**: When no functional processes exist in the specification, the engine MUST still produce a result from CSM and non-process CFM elements, accompanied by an informational notice.

- **FR-014**: Duplicate functional processes (content-identical by fingerprint) MUST be deduplicated and counted in execution metadata without inflating the total score.

### Key Entities

- **Functional Work Item**: Represents the estimation result for a single element. Contains the element identifier, name, raw score (before normalization), normalized Fibonacci value, structural score breakdown (factor contributions or base weight), content token count, content-based score contribution, and evidence references.

- **Story Points Measurement Result**: Aggregated result for a specification. Contains the run identifier, method name, Fibonacci scale designation, total normalized points, list of all work items, distribution histogram of normalized values, specification effort total (CSM-derived), implementation effort total (CFM-derived), per-type content token breakdown, content multiplier value, calibration version, execution metadata, informational notices, and measurement timestamp.

- **Story Points Calibration Profile**: External configuration containing factor coefficients, element base weights, content multiplier, default fallback weight, Fibonacci output scale values, and ranking strategy. All fields have documented defaults enabling backward-compatible loading. Normalization is relative (rank-based), not threshold-based.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Two specifications with identical functional process structures but one having 3x the description content volume produce raw scores where the content-richer specification is at least 1.3x higher than the leaner one.

- **SC-002**: A specification containing at least 3 distinct CSM element types and 3 distinct non-process CFM element types produces a measurement result where the detailed breakdown shows contributions from all 6 element types, verifiable through the output report.

- **SC-003**: The measurement output report contains the content multiplier value, per-type content token breakdown, and separate specification effort vs. implementation effort totals, all directly visible to the user in the standard output.

- **SC-004**: Running Story Points on any specification with content multiplier set to 0.0 produces raw scores that match the current factor-only engine output exactly — the content-based component contributes zero and all other calculations remain unchanged.

- **SC-005**: An element type not present in the calibration base weight table uses the default fallback weight and generates an informational notice visible in the output.

- **SC-006**: A calibration profile from the previous version (lacking content multiplier and base weight fields) loads without errors and produces results using the documented defaults.

- **SC-007**: Two specifications from different SDD frameworks (SpecKit and OpenSpec) with similar total content volume produce total raw scores differing by less than 15%.

- **SC-008**: The Story Points RFC document describes the full estimation formula, all element types with their default base weights and rationale, the relative-ranking Fibonacci normalization approach, and guidance on using Story Points for cross-specification comparison and manual Kanban work item sizing.

## Assumptions

- The shared token counting utility is already implemented and available for consumption by the Story Points engine, as it is already used by Token Points and Cognitive Points.
- The existing 6-factor weighted sum for functional processes remains the correct structural estimation model. Content-based estimation is additive, not a replacement.
- The Modified Fibonacci scale (1, 2, 3, 5, 8, 13, 20, 40, 100) is retained as the output scale. Normalization uses relative ranking of raw scores within the specification rather than fixed thresholds, making scores relative to other entities in the same specification.
- The Canonical Specification Model (CSM) already contains activities, decisions, assumptions, constraints, risks, open questions, acceptance criteria, glossary terms, and references as structured data accessible to measurement plugins.
- Specification decomposition into equal-effort work items is a manual Kanban practice performed by the user. SpecMetrics provides the comparability data that enables this practice but does not implement automatic chunking or splitting functionality.
- Calibration profiles are designed to be extensible — new optional parameters can be added with sensible defaults so that existing profiles continue to work without modification.
- A dedicated RFC document for Story Points will be created following the same documentation patterns established by existing RFCs (Token Points, Cognitive Points).
- The deduplication mechanism for functional processes (content fingerprinting) is already implemented and will continue to work with the extended scoring formula.
