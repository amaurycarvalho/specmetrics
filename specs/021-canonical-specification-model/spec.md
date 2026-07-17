# Feature Specification: Canonical Specification Model Builder

**Feature Branch**: `021-canonical-specification-model`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "Canonical Specification Model (CSM)"

## Clarifications

### Session 2026-07-17

- Q: How should core CSM entities (Decision, Assumption, Constraint, Risk, OpenQuestion, AcceptanceCriterion, GlossaryTerm) be structured? → A: Entities inherit from a common CsmElement base (id, description, evidence_references), each adding type-specific fields.
- Q: How should CSM elements be uniquely identified? → A: UUID v4 assigned at creation.
- Q: What form should the CSM query interface take? → A: Category-based query methods (e.g., `get_elements(category)` and `get_by_evidence(ref)`).
- Q: Should non-SpecificationActivity entities have status/lifecycle fields? → A: Yes, all entities share a common `status` field (Active, Superseded) defined in CsmElement base.
- Q: What serialization format should the CSM use for inspection/debugging? → A: JSON via Pydantic model_dump_json.

---

# User Scenarios & Testing _(mandatory)_

## User Story 1 - Transform evidence graph into canonical specification model (Priority: P1)

A pipeline operator runs the measurement pipeline. After the Evidence Graph stage completes, the CSM Builder automatically transforms the evidence graph into a framework-independent Canonical Specification Model containing the semantic characteristics of the specification process itself, such as Decisions, Assumptions, Constraints, Open Questions, Risks, Acceptance Criteria, Glossary Terms, and Specification Activities. The output is independent of any specific SDD framework.

**Why this priority**

The Canonical Specification Model becomes the architectural boundary between specification frameworks and specification-quality analysis. Downstream engines (Token Points, Cognitive Points, quality analyzers) consume only the CSM, never framework-specific artifacts.

**Independent Test**

Provide an evidence graph extracted from both OpenSpec and SpecKit repositories containing specification artifacts (Explore, Clarify, Decisions, Questions, Assumptions). Verify that the resulting CSM contains only canonical elements with no framework-specific terminology.

### Acceptance Scenarios

1. **Given** an evidence graph containing SpecKit Clarify questions and OpenSpec Explore decisions, **When** the CSM Builder transforms the graph, **Then** both are normalized into canonical Specification Activities and Decision elements.

2. **Given** an evidence graph containing framework-specific concepts such as "Clarify Session" or "Explore Phase", **When** the CSM Builder processes the graph, **Then** the resulting CSM contains only canonical concepts with preserved evidence references.

3. **Given** evidence references attached to every extracted specification element, **When** the CSM Builder completes, **Then** every CSM element preserves full provenance to the originating specification.

---

## User Story 2 - Inspect specification maturity and quality (Priority: P1)

A specification author or reviewer inspects the Canonical Specification Model to understand how the specification evolved, which assumptions remain unresolved, which decisions were taken, and where cognitive complexity originates.

**Why this priority**

Measurement engines require trustable specification metadata before estimating token consumption or human validation effort.

**Independent Test**

Generate a known specification containing assumptions, risks, decisions, glossary terms and acceptance criteria. Verify that each element appears in the appropriate CSM category with complete traceability.

### Acceptance Scenarios

1. **Given** a CSM, **When** an analyst enumerates all Open Questions, **Then** every unresolved question is returned with its originating evidence.

2. **Given** a Decision element, **When** the analyst inspects its provenance, **Then** the complete evidence chain is available.

3. **Given** multiple Assumptions derived from different documents, **When** the analyst queries the CSM, **Then** all assumptions are presented independently of the originating SDD framework.

---

## User Story 3 - Feed downstream specification measurement engines (Priority: P2)

A measurement engine developer implements Token Points or Cognitive Points using only the Canonical Specification Model without any knowledge of OpenSpec, SpecKit or future specification frameworks.

**Why this priority**

Specification-oriented measurements must remain framework-independent, preserving the plugin architecture defined by SpecMetrics.

**Independent Test**

Implement a mock measurement engine consuming only the CSM interface and verify identical behavior for repositories created using different specification frameworks.

### Acceptance Scenarios

1. **Given** two repositories specified using different SDD frameworks, **When** the CSM Builder processes both, **Then** the resulting CSM structure is identical although the evidence differs.

2. **Given** a downstream engine consuming the CSM, **When** it calculates specification metrics, **Then** no framework-specific imports or metadata are required.

---

# Edge Cases

- What happens when a specification contains contradictory Decisions? Both Decisions are preserved and flagged as conflicting in the build metadata.
- What happens when an Assumption later becomes a confirmed Business Rule? Both elements remain preserved with their evidence chain and are linked through a semantic relationship.
- What happens when no specification-process artifacts exist? The builder produces an empty Canonical Specification Model and completes successfully.
- What happens when framework-specific concepts have no canonical equivalent? They are preserved in the References category to avoid information loss.

---

# Constitution Check _(mandatory)_

**Engaged Principles**: VII (Canonical Representation), XIV (Layer Independence), V (Evidence First)

**Compliance Notes**

- Canonical Representation (VII): The CSM removes all framework-specific terminology while preserving the semantic intent of specification activities.
- Layer Independence (XIV): Downstream engines consume only the CSM contract.
- Evidence First (V): Every CSM element preserves complete provenance back to the original specification.

---

# Requirements _(mandatory)_

## Functional Requirements

### Core Model

- **FR-001**: The CSM Builder MUST consume an EvidenceGraph and produce an immutable CanonicalSpecificationModel.

- **FR-002**: Every CSM element MUST preserve complete evidence references (document, section, fragment).

- **FR-003**: The CanonicalSpecificationModel MUST NOT expose framework-specific terminology.

### Canonical Categories

The CanonicalSpecificationModel MUST organize specification knowledge into the following canonical categories.

- **FR-004**: Specification Activities
- **FR-005**: Decisions
- **FR-006**: Assumptions
- **FR-007**: Constraints
- **FR-008**: Risks
- **FR-009**: Open Questions
- **FR-010**: Acceptance Criteria
- **FR-011**: Glossary Terms
- **FR-012**: References (fallback category)

### Classification

- **FR-013**: The builder MUST classify extracted specification elements into canonical categories using deterministic semantic rules.

- **FR-014**: Elements that cannot be classified MUST be preserved in References.

- **FR-015**: Classification conflicts MUST be reported in build metadata without failing the pipeline.

### Immutability

- **FR-016**: The CanonicalSpecificationModel MUST be immutable after construction.

### Pipeline

- **FR-017**: Upon successful completion the builder MUST emit a structured event `CanonicalSpecificationModelBuilt`.

### Query Interface

- **FR-018**: The CSM MUST expose a documented category-based query interface (e.g., `get_elements(category)`, `get_by_evidence(reference)`) allowing downstream engines to enumerate categories, query by evidence reference and traverse semantic relationships.

---

# Key Entities _(include if feature involves data)_

## CanonicalSpecificationModel

Top-level immutable representation of specification knowledge.

Contains canonical collections for:

- Specification Activities
- Decisions
- Assumptions
- Constraints
- Risks
- Open Questions
- Acceptance Criteria
- Glossary Terms
- References

---

## SpecificationActivity

Represents an activity performed while constructing or refining the specification.

Examples:

- Exploration
- Clarification
- Refinement
- Review
- Validation

---

## CsmElement (Base)

Shared base inherited by all canonical entities. Contains:

- **id**: UUID v4 unique identifier within the model
- **description**: Semantic content of the element
- **evidence_references**: Provenance links to originating specification fragments
- **status**: Lifecycle state (Active, Superseded)

---

## Decision

A documented architectural, business or specification decision. Inherits CsmElement.

Additional attributes:
- **rationale**: Justification for the decision
- **alternatives**: Considered options
- **timestamp**: When the decision was documented

---

## Assumption

A statement accepted as true during specification but not yet validated. Inherits CsmElement.

Additional attributes:
- **validated_date**: When the assumption was confirmed, if applicable

---

## Constraint

A limitation imposed on the solution. Inherits CsmElement.

Additional attributes:
- **constraint_type**: Category (Regulatory, Technical, Organizational)
- **source**: Origin of the constraint

---

## Risk

A documented uncertainty that may impact implementation or specification quality. Inherits CsmElement.

Additional attributes:
- **probability**: Likelihood assessment
- **impact**: Potential consequence
- **mitigation**: Planned or applied countermeasure

---

## OpenQuestion

A question intentionally left unresolved during specification. Inherits CsmElement.

Additional attributes:
- **resolved**: Whether the question has been answered
- **resolution**: Answer details if resolved

---

## AcceptanceCriterion

A verifiable condition describing expected system behavior. Inherits CsmElement.

Additional attributes:
- **verification_method**: How the criterion is verified (Test, Review, Inspection)

---

## GlossaryTerm

A domain concept with an agreed semantic definition. Inherits CsmElement.

Additional attributes:
- **aliases**: Alternative names for the concept

---

## BuildMetadata

Diagnostic information including:

- category counts
- build duration
- unclassified elements
- classification conflicts

---

# Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: An evidence graph containing 500 specification-related elements is transformed into a CSM in under 3 seconds.

- **SC-002**: A CSM generated from different SDD frameworks contains zero framework-specific concepts.

- **SC-003**: 100% of CSM elements preserve complete provenance.

- **SC-004**: Downstream consumers enumerate every canonical category without depending on framework-specific modules.

- **SC-005**: All unclassifiable specification elements are preserved in References.

- **SC-006**: Building the CSM twice from identical evidence graphs produces byte-equivalent models.

---

# Assumptions

- The Semantic Extraction stage identifies specification-process semantics (questions, decisions, assumptions, constraints, risks, glossary terms, acceptance criteria and refinement activities) in addition to functional semantics.
- OpenSpec, SpecKit and future specification frameworks expose sufficient evidence for deterministic normalization into the Canonical Specification Model.
- The CSM is an immutable in-memory model with JSON serialization (via Pydantic model_dump_json) for inspection and debugging.
- The primary downstream consumers of the CSM are Token Points, Cognitive Points and future specification-quality measurement engines.
- The CSM is independent of the Canonical Functional Model, although both originate from the same Evidence Graph and may be consumed jointly by downstream measurement engines.

---

## SpecificationActivity

Represents a canonical activity performed during the specification lifecycle. Specification Activities capture the work required to progressively transform an initial idea into a complete, validated, and implementation-ready specification.

This entity abstracts framework-specific concepts such as OpenSpec _Explore_ and SpecKit _Clarify_ into a unified representation that can be analyzed independently of the originating specification framework.

A SpecificationActivity may represent one of several canonical activity types, including:

- **Exploration** — discovering requirements, business context, domain concepts, and alternative solutions.
- **Clarification** — resolving ambiguities, answering open questions, and refining incomplete requirements.
- **Refinement** — improving the structure, consistency, completeness, or precision of existing specifications.
- **Review** — evaluating the specification for correctness, consistency, traceability, and quality.
- **Validation** — confirming that the specification satisfies stakeholder intent and is ready for implementation.

Each SpecificationActivity preserves its evidence references and may be semantically linked to other CSM entities such as Decisions, Assumptions, Constraints, Risks, Open Questions, Acceptance Criteria, and Glossary Terms.

Typical attributes include:

- **activity_type** — Canonical activity classification (Exploration, Clarification, Refinement, Review, Validation).
- **status** — Current lifecycle state (e.g., Open, In Progress, Completed, Superseded).
- **evidence_references** — Provenance information linking the activity to its originating specification fragments.
- **linked_decisions** — Decisions produced or modified during the activity.
- **linked_questions** — Open Questions created or resolved.
- **linked_assumptions** — Assumptions introduced or validated.
- **linked_constraints** — Constraints identified or refined.
- **linked_risks** — Risks discovered or mitigated.
- **linked_acceptance_criteria** — Acceptance Criteria created or updated.

By normalizing specification work into SpecificationActivity, the Canonical Specification Model provides a framework-independent representation of the specification process itself. This enables downstream measurement engines—such as Token Points and Cognitive Points—to estimate computational cost and human cognitive effort based not only on the resulting specification, but also on the amount and nature of the work required to produce it.
