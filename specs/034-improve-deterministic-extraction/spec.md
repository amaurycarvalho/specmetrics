# Feature Specification: Improve Deterministic Extraction Engine for Complete Metric Coverage

**Feature Branch**: `034-improve-deterministic-extraction`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Diagnóstico completo: por que cada métrica mostrava 0. Causa raiz #3: Nenhuma regra de extração para type=operation no motor determinístico. Causa raiz #4: SNAP não tem semantic_marker nos metadados. Causa raiz #5: Classificador não identifica atores. As 4 métricas que permanecem em 0 dependem de operations/functional_processes/semantic_marker que o motor determinístico atual não produz."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operation Extraction for GWT Scenarios (Priority: P1)

A user running `specmetrics measure` without an LLM (deterministic fallback) on a SpecKit project expects the deterministic engine to identify user interactions (operations) from Given/When/Then acceptance scenarios, so that functional processes can be built and metrics like Story Points, BCP, and transactional FPA (EI/EO/EQ) produce non-zero counts.

**Why this priority**: Operations are the backbone of functional processes. Without them, 5 out of 8 metrics (Story Points, BCP, TShirt, and the transactional side of FPA/SFP) produce zero results. This is the highest-impact gap.

**Independent Test**: Run `specmetrics measure` on a SpecKit project with GWT scenarios (e.g., `specs/008-measurement-engine-fpa/spec.md`). Verify that the CFM contains at least one functional process with linked operations, and that Story Points and BCP produce non-zero totals.

**Acceptance Scenarios**:

1. **Given** a SpecKit specification containing `**GIVEN**: ... **WHEN**: ... **THEN**: ...` patterns, **When** the deterministic engine extracts elements, **Then** at least one element is produced with `type="operation"` and the operation direction is inferred from the GWT keyword (GIVEN/WHEN → input, THEN → output).

2. **Given** extracted operation elements in the evidence graph, **When** the CFM builder processes the graph, **Then** operations are grouped by document into functional processes, each with a non-empty `operation_ids` list.

3. **Given** a CFM with functional processes, **When** the FPA measurement engine runs, **Then** transactional function types (EI, EO, EQ) are counted based on operation direction, adding to the existing ILF counts from data groups.

---

### User Story 2 - SNAP Semantic Marker Inference (Priority: P2)

A user running `specmetrics measure` expects the SNAP (Software Non-functional Assessment Process) measurement to classify CFM elements into non-functional categories (presentation, data operations, operational capabilities, technical interaction) based on the element's document section and semantic type, rather than producing zero items with 1005 warnings.

**Why this priority**: SNAP is one of the 8 supported measurement methodologies but currently always returns zero on deterministic runs. Enabling it provides a complete non-functional measurement dimension alongside functional metrics.

**Independent Test**: Run `specmetrics measure` on a SpecKit project with diverse specification sections. Verify that SNAP produces at least one classified item (non-zero `snap_total_items`) and that no `MISSING_SEMANTIC_MARKER` warnings remain for elements that should be classifiable.

**Acceptance Scenarios**:

1. **Given** a data group element originating from a "Data Model" or "Key Entities" section, **When** the CFM builder constructs the element, **Then** its metadata includes `semantic_marker: "data_operation"`.

2. **Given** a business rule element originating from a "User Scenarios" or "Functional Requirements" section, **When** the CFM builder constructs the element, **Then** its metadata includes `semantic_marker: "operational_feature"`.

3. **Given** CFM elements with `semantic_marker` metadata, **When** SNAP measurement runs, **Then** elements are classified into the appropriate SNAP category and contribute to the total SNAP score.

---

### User Story 3 - Actor Identification from Specification Entities (Priority: P3)

A user running `specmetrics measure` expects the deterministic engine to correctly identify system actors (users, roles, external systems) from specification entities, rather than classifying all entities as data groups. This enriches functional processes with actor associations, improving measurement quality for FPA transactional complexity and Story Points business interaction scoring.

**Why this priority**: Actor identification improves measurement quality (complexity ratings, business interaction scoring) but is not strictly required for metrics to become non-zero — operations alone enable functional processes. This is a quality improvement.

**Independent Test**: Run `specmetrics measure` on a SpecKit project containing actor definitions (e.g., headings like "Actors", entity descriptions with role keywords). Verify that the CFM contains at least one Actor element, and that functional processes have non-empty `actor_ids`.

**Acceptance Scenarios**:

1. **Given** an entity element with text matching an actor name pattern (e.g., "User", "Admin", "System"), **When** the CFM classifier processes the entity, **Then** the element is classified as `actor` instead of `data_group`.

2. **Given** actors associated with a functional process, **When** Story Points measurement runs, **Then** the `business_interactions` factor score reflects the number of linked actors (non-zero when actors exist).

---

### Edge Cases

- What happens when a document has GWT scenarios but no recognizable GIVEN/WHEN/THEN pattern (e.g., bullet lists instead of bold keywords)?
- How does the system handle markdown documents with code blocks containing GWT-like strings (false positives)?
- What happens when an entity name matches both actor and data group patterns (e.g., "Report Manager")?
- How does SNAP handle elements from sections that don't match any semantic marker mapping?
- What happens when the deterministic engine processes a mixed project (some SpecKit, some plain markdown)?

## Constitution Check *(mandatory)*

**Engaged Principles**:
- **III. Semantic Before Structural**: The classifier improvements prioritize semantic understanding (actor roles, operation semantics) over document structure.
- **IV. LLM-Assisted, Deterministic Results**: All extraction and classification improvements apply to the deterministic fallback engine, ensuring it remains a viable alternative to LLM extraction.
- **V. Evidence First**: All new element types (operations, actors) maintain traceability through the evidence graph.
- **VII. Canonical Representation**: Improvements operate on the CFM, not framework-specific artifacts.
- **IX. Rule Externalization**: Operation extraction rules are added to external YAML rule packs, not hardcoded in the engine.

**Compliance Notes**:
- Operation extraction rules follow the existing rule pack format (`default_rule_pack.yaml`, `speckit_rules.yaml`).
- Semantic marker inference is implemented in the CFM builder, applying deterministic heuristics based on element type and document section context.
- Actor classification improvements extend the existing `_classify_entity()` function, preserving the existing category taxonomy.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The deterministic extraction engine MUST support `type: "operation"` rules in its rule packs, producing `ExtractedElement` instances with semantic type `"operation"`.
- **FR-002**: Operation extraction rules MUST detect operations from SpecKit GWT patterns: `**GIVEN**`, `**WHEN**`, `**THEN**` keywords appearing in specification documents. OpenSpec operation extraction is out of scope for this feature.
- **FR-003**: Operation extraction rules MUST infer operation direction from the matched keyword: GIVEN and WHEN map to `"input"`, THEN maps to `"output"`.
- **FR-004**: The CFM builder MUST construct `FunctionalProcess` entities grouping operations by their evidence `document_id`, even when a document has only a single operation.
- **FR-005**: The CFM builder MUST infer `semantic_marker` metadata for each element based on the element's CFM type and the document section context from its evidence reference.
- **FR-006**: SNAP semantic marker inference MUST support at least four categories: `presentation_interface`, `data_operation`, `operational_feature`, and `technical_interface`.
- **FR-007**: Default marker-to-section mappings MUST be documented and overridable via rule packs or configuration.
- **FR-008**: The entity classifier (`_classify_entity`) MUST identify actors from entity names that match known role keywords (e.g., "User", "Admin", "Operator") or end with role suffixes ("-er", "-or", "-ist").
- **FR-009**: When an entity name matches both actor and data group patterns, the actor classification MUST take precedence to avoid false data group assignments.
- **FR-010**: All new extraction and classification logic MUST preserve evidence references (document_id, section_id, graph_node_id) for every generated element.

### Key Entities

- **Operation**: A transactional action extracted from specifications. Has a direction (input/output/query) inferred from the matched pattern. Links to a parent functional process via `parent_process_id`.
- **Functional Process**: A grouping of related operations within a single specification document. Acts as the bridge between extracted elements and measurement engines.
- **Actor**: A role or external system that interacts with functional processes. Identified by name patterns from entity extraction.
- **Semantic Marker**: A metadata tag on CFM elements that maps them to SNAP categories (presentation, data operations, operational capabilities, technical interaction).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `specmetrics measure` without LLM on the SpecMetrics project itself produces at least 1 functional process in the CFM (currently 0).
- **SC-002**: Story Points measurement returns a non-zero total (currently 0) after operation extraction rules are added.
- **SC-003**: SNAP measurement produces non-zero classified items (currently 0 items, 1005 warnings) after semantic marker inference.
- **SC-004**: FPA transactional function count (EI + EO + EQ) is non-zero (currently 0 operations → 0 transactional functions).
- **SC-005**: The CFM contains at least 1 Actor entity when processing specifications that contain role descriptions or actor sections.
- **SC-006**: All extracted elements (operations, actors) maintain traceability through the evidence graph, with no broken or missing `evidence` references.

## Clarifications

### Session 2026-07-20

- Q: Should operation extraction apply to both SpecKit and OpenSpec, or SpecKit-only? → A: SpecKit only. Add `type: "operation"` rules to `speckit_rules.yaml` and `default_rule_pack.yaml`; defer OpenSpec to a later iteration.

## Assumptions

- The SpecKit framework GWT patterns use bold markdown syntax (`**GIVEN**`, `**WHEN**`, `**THEN**`) as the primary operation indicators. Variations using non-bold formats may not be detected in the initial implementation.
- Semantic marker inference uses a deterministic mapping from document section identifiers (e.g., "Data Model", "User Scenarios", "Key Entities") to SNAP categories. This mapping can be extended via rule packs in future iterations.
- Actor classification heuristics (role keywords, suffixes) are sufficient for the SpecKit project's own specifications. Domain-specific actor names may require custom rule packs.
- The existing rule pack infrastructure (`YAML` rule packs loaded by `RulePackLoader`) is the appropriate extension point for operation rules, consistent with Principle IX (Rule Externalization).
- Metrics that remain at zero due to missing data (e.g., BCP when SDK is unavailable) are outside scope — this feature only addresses extraction gaps.
- OpenSpec operation extraction rules are deferred to a future iteration. This feature focuses on SpecKit pattern detection only.
