# Feature Specification: OpenSpec Operation Extraction Rules

**Feature Branch**: `035-openspec-operation-rules`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Crie uma nova feature para implementar o OpenSpec operation extraction rules, tal como foi feito para o SpecKit via o 034-improve-deterministic-extraction." The OpenSpec framework uses a change-based document model (proposal.md, design.md, tasks.md, and delta specs) with its own heading hierarchy, GWT scenario format, and behavioral statement patterns that the deterministic engine must interpret as operations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repurpose Fact-Rules as Operation-Rules (Priority: P1)

A user running `specmetrics measure` on an OpenSpec project expects the deterministic engine to classify system behaviors (THEN assertions, SHALL/DEVE behavioral statements, AND continuation clauses) as operations, not generic facts, so that functional processes can be built and all measurement metrics produce non-zero counts.

**Why this priority**: OpenSpec already has 2 operation rules (scenario headings and WHEN triggers) producing some operations, but 9 existing rules produce `type: "fact"` for clearly behavioral content (THEN, AND, SHALL, DEVE, requirement headings, etc.). Changing these to `type: "operation"` is the simplest, highest-impact change — it directly enables functional process construction and non-zero metrics without adding new rules.

**Independent Test**: Run `specmetrics measure` on the OpenSpec test samples at `tests/openspec/`. Verify that the CFM contains at least one functional process with linked operations, and that Story Points, BCP, and transactional FPA produce non-zero totals.

**Acceptance Scenarios**:

1. **Given** an OpenSpec specification containing `- **THEN** the system SHALL display the panel` clauses inside `#### Scenario:` blocks, **When** the deterministic engine extracts elements, **Then** the THEN clause produces an element with `type="operation"` (not `"fact"`) and direction `"output"`.

2. **Given** an OpenSpec specification containing `- **AND** the system SHALL ALSO log the event` clauses, **When** the deterministic engine extracts elements, **Then** the AND clause produces an element with `type="operation"`.

3. **Given** a requirement body containing `O sistema DEVE calcular o z-score combinado` (Portuguese behavioral statement), **When** the deterministic engine extracts elements, **Then** the DEVE statement produces an element with `type="operation"`.

---

### User Story 2 - Detect GWT Scenario Context for Direction Inference (Priority: P2)

A user running `specmetrics measure` on an OpenSpec project expects the operation direction (input/output) to be correctly inferred from the GWT context. Given statements indicate preconditions (input), When statements indicate triggers (input), Then statements indicate outcomes (output), and And statements should continue the direction of their preceding sibling.

**Why this priority**: The CFM builder's `_infer_operation_direction()` already handles GIVEN/WHEN → input and THEN → output patterns. Ensuring OpenSpec rules produce operations with text that matches these patterns is necessary for correct FPA transactional function classification (EI vs EO vs EQ). Without correct direction, FPA may misclassify transactions.

**Independent Test**: Run `specmetrics measure` on an OpenSpec spec containing all GWT types. Verify that operations from WHEN clauses have direction "input" and operations from THEN clauses have direction "output" in the CFM.

**Acceptance Scenarios**:

1. **Given** an operation extracted from a `- **WHEN** user clicks the button` clause, **When** the CFM builder processes the operation, **Then** the operation metadata includes `direction: "input"`.

2. **Given** an operation extracted from a `- **THEN** the panel SHALL display the result` clause, **When** the CFM builder processes the operation, **Then** the operation metadata includes `direction: "output"`.

---

### User Story 3 - Extract Operations from Requirement Headings (Priority: P3)

A user running `specmetrics measure` expects the deterministic engine to treat OpenSpec requirement headings (`### Requirement: Title (ID)`) as named operations, since each requirement describes a specific system behavior or capability. These headings provide a higher-level operation abstraction that complements the granular scenario-level operations.

**Why this priority**: Requirement headings name system behaviors at the capability level. Treating them as operations enriches the functional process model with parent-level operations. This is a quality improvement — scenario-level operations (US1) already provide the core functionality.

**Independent Test**: Run `specmetrics measure` on an OpenSpec spec. Verify that requirement headings (`### Requirement:`) produce operation elements, and the functional process has operations at both the requirement and scenario level.

**Acceptance Scenarios**:

1. **Given** an OpenSpec specification with `### Requirement: DiagnosisPanel replaces Resumo Geral (DP101)`, **When** the deterministic engine extracts elements, **Then** the heading produces an element with `type="operation"` and content "DiagnosisPanel replaces Resumo Geral".

2. **Given** requirement-heading operations and scenario-level operations from the same spec, **When** the CFM builder constructs functional processes, **Then** both levels of operations appear in the functional process's operation list.

---

### Edge Cases

- What happens when an AND clause follows a WHEN (input) vs a THEN (output)? In v1, AND clauses default to "input" direction regardless of context. Direction inheritance from sibling context is deferred to a future feature.
- How does the system handle `- **SHALL NOT** ...` or `- **NÃO DEVE** ...` negation statements? Should they still be operations?
- What happens with OpenSpec delta specs that contain both `ADDED` and `MODIFIED` requirement sections?
- How are scenarios that contain only WHEN and AND (no explicit THEN) handled?
- What about bilingual documents mixing Portuguese (DEVE) and English (SHALL)?

## Clarifications

### Session 2026-07-20

- Q: Should AND clause direction inheritance from sibling context be fixed in v1, or is builder default fallback acceptable? → A: Defer — accept builder default for v1. AND clauses get default direction "input" regardless of context. Direction inference enhancement is a separate feature.

## Constitution Check *(mandatory)*

**Engaged Principles**:
- **III. Semantic Before Structural**: Repurposing existing rules from `type: "fact"` to `type: "operation"` is a semantic correction — THEN clauses ARE operations, not generic facts.
- **IV. LLM-Assisted, Deterministic Results**: All changes apply to the deterministic fallback engine. Rules are YAML-based, not LLM-dependent.
- **V. Evidence First**: No new element types — existing extraction preserves evidence references.
- **VII. Canonical Representation**: Operations flow through the CFM to all measurement engines.
- **IX. Rule Externalization**: Changes are confined to `openspec_rules.yaml` — no engine code changes.

**Compliance Notes**:
- Rule type changes are minimal: `"fact"` → `"operation"` in existing YAML entries. No new rule infrastructure needed.
- Direction inference is already handled by the CFM builder (`_infer_operation_direction`) for GWT keywords.
- Existing evidence reference mechanism is preserved unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `openspec-then-assertion` rule MUST change from `type: "fact"` to `type: "operation"` so THEN clauses are classified as operations with output direction.
- **FR-002**: The `openspec-and-clause` rule MUST change from `type: "fact"` to `type: "operation"` so AND continuation clauses are classified as operations.
- **FR-003**: The `openspec-shall-statement` rule MUST change from `type: "fact"` to `type: "operation"` so SHALL behavioral statements are classified as operations.
- **FR-004**: The `openspec-deve-statement` rule MUST change from `type: "fact"` to `type: "operation"` so DEVE behavioral statements are classified as operations.
- **FR-005**: The `openspec-task-item` rule MUST change from `type: "fact"` to `type: "operation"` so task checkboxes (implementation actions) are classified as operations.
- **FR-006**: The `openspec-decision-colon` rule MUST change from `type: "fact"` to `type: "operation"` so design decisions are classified as operations.
- **FR-007**: The `openspec-what-changes` rule MUST change from `type: "fact"` to `type: "operation"` so change descriptions are classified as operations.
- **FR-008**: The `openspec-req-heading` rule MUST change from `type: "fact"` to `type: "operation"` so requirement headings are classified as named operations.
- **FR-009**: The `openspec-task-category` rule MUST change from `type: "fact"` to `type: "operation"` so task categories are classified as operations.
- **FR-010**: Running `specmetrics measure` on OpenSpec test samples MUST produce at least one functional process in the CFM.

### Key Entities

- **Operation**: Already defined in the CFM. Direction is inferred by the builder from GWT keywords in the element text. WHEN/GIVEN → input, THEN → output.
- **OpenSpec Rule**: A YAML entry in `openspec_rules.yaml` defining a pattern match. Type changes from `"fact"` to `"operation"` alter only the semantic classification, not the extraction logic.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `specmetrics measure` on the OpenSpec test samples produces at least 1 functional process in the CFM.
- **SC-002**: Story Points measurement returns a non-zero total for OpenSpec projects.
- **SC-003**: FPA transactional function count (EI + EO + EQ) is non-zero for OpenSpec projects.
- **SC-004**: All 9 repurposed rules produce elements with `type="operation"` (verified by inspecting extracted element types).
- **SC-005**: Operation direction is correctly inferred: WHEN clauses → "input", THEN clauses → "output", verified in CFM operation metadata.
- **SC-006**: No existing OpenSpec extraction behavior is broken — all previously extracted fact-type elements from unchanged rules are preserved.

## Assumptions

- The existing `openspec-scenario-heading` and `openspec-when-trigger` rules (already typed as `"operation"`) are correct and do not need modification.
- The CFM builder's `_infer_operation_direction()` already handles GIVEN/WHEN → input, THEN → output, and Scenario: → query. No builder code changes needed.
- AND clauses that follow a WHEN should have direction "input", and AND clauses that follow a THEN should have direction "output". The builder can't distinguish this context; AND clauses default to the builder's generic direction. This is acceptable for v1. Direction inheritance from sibling context is deferred to a future feature.
- Portuguese DEVE statements and English SHALL statements are semantically equivalent (both express mandatory behavior) and should both be typed as operations.
- Task items and decision records, while not behavioral operations in the strict sense, provide valuable structural operations that enrich the functional process model.
