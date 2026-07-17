# Feature Specification: Measurement Engine Plugin — Token Points

**Feature Branch**: `022-measurement-engine-token-points`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "Token Points"

## Clarifications

### Session 2026-07-17

- Q: What format should calibration profiles use? → A: YAML (via ruamel.yaml).
- Q: How should weights be structured in the CalibrationProfile? → A: Hierarchical — nested by cost component (specification_cost, code_generation_cost) with per-type weights.
- Q: What attributes should SpecificationCost and CodeGenerationCost have? → A: Total cost value + list of TokenContributions.
- Q: How should a measurement be uniquely identified? → A: Run ID inherited from pipeline execution.
- Q: How should individual weighted contributions be aggregated? → A: Simple sum of weighted element counts (Σ weight × 1.0 per element).

---

# User Scenarios & Testing _(mandatory)_

## User Story 1 - Estimate AI computational cost for a specification (Priority: P1)

A technical leader executes the SpecMetrics measurement pipeline and receives a Token Points measurement representing the expected computational cost of implementing a specification using LLM-assisted software engineering. The estimate includes both the specification effort and the expected code generation effort.

**Why this priority**

Token budget has become a first-class engineering resource. Teams need deterministic estimates before implementation begins to support planning, budgeting and prioritization.

**Independent Test**

Execute the measurement pipeline against a known specification and verify that Token Points are deterministically calculated from the Canonical Functional Model (CFM), Canonical Specification Model (CSM), and configured weighting rules.

### Acceptance Scenarios

1. **Given** a specification containing functional processes, business rules, and multiple clarification activities, **When** the Token Points engine executes, **Then** it produces a deterministic Token Points estimate and a complete breakdown of contributing factors.

2. **Given** identical specifications executed multiple times, **When** Token Points are calculated, **Then** the resulting score is identical.

3. **Given** different specification frameworks (OpenSpec and SpecKit), **When** equivalent specifications are measured, **Then** Token Points are independent of the originating framework.

---

## User Story 2 - Understand where token consumption originates (Priority: P1)

A software architect analyzes a Token Points report to understand which aspects of the specification contribute most to expected token consumption.

**Why this priority**

Token estimation must be explainable. Users need to understand why one specification is significantly more expensive than another.

**Independent Test**

Inspect the generated report and verify that every Token Points contribution is traceable to specific CFM or CSM elements.

### Acceptance Scenarios

1. **Given** a measurement result, **When** the architect inspects the Token Points breakdown, **Then** every contribution references its originating canonical elements.

2. **Given** an unusually high Token Points score, **When** the report is inspected, **Then** the dominant contributors are explicitly identified.

3. **Given** configured weighting rules, **When** the calculation is executed, **Then** every applied weight is reported.

---

## User Story 3 - Support planning and AI budget forecasting (Priority: P2)

A Product Manager aggregates Token Points across a backlog to estimate the expected AI token budget required for an iteration, sprint, or Program Increment (PI).

**Why this priority**

Engineering organizations increasingly allocate AI usage budgets similarly to staffing budgets. Token Points provide a planning metric before implementation begins.

**Independent Test**

Aggregate Token Points from multiple specifications and verify deterministic project-level totals.

### Acceptance Scenarios

1. **Given** multiple measured specifications, **When** Token Points are aggregated, **Then** the total equals the sum of individual measurements.

2. **Given** weighting configuration changes, **When** measurements are recalculated, **Then** the new estimates reflect the updated calibration.

---

# Edge Cases

- What happens when no Specification Activities exist? Specification Cost is zero while Code Generation Cost is still calculated from the CFM.
- What happens when the CFM is empty? Token Points are computed only from specification-related activities.
- What happens when weighting configuration is missing? The engine loads the built-in default calibration.
- What happens when unknown semantic elements are encountered? They contribute no score and are reported in the measurement metadata.

---

# Constitution Check _(mandatory)_

**Engaged Principles**: VII (Canonical Representation), VIII (Plugin-Oriented Architecture), V (Evidence First), XV (Deterministic Measurement)

**Compliance Notes**

- Consumes only canonical models (CFM and CSM).
- Produces deterministic measurements.
- Every score is fully traceable.
- Calibration is externalized through Rule Packs.

---

# Requirements _(mandatory)_

## Functional Requirements

### Measurement Engine

- **FR-001**: The Token Points engine MUST be implemented as a Measurement Engine plugin.

- **FR-002**: The engine MUST consume the Canonical Functional Model (CFM) and the Canonical Specification Model (CSM).

- **FR-003**: The engine MUST produce a deterministic Token Points measurement.

---

### Measurement Model

- **FR-004**: Token Points MUST represent the estimated computational effort required for AI-assisted software engineering.

- **FR-005**: The measurement MUST be composed of two independent components:
  - Specification Cost
  - Code Generation Cost

- **FR-006**: The engine MUST calculate

```
Token Points = Specification Cost + Code Generation Cost
```

Where each component is the simple sum of weighted element contributions: Σ(weight × 1.0) per canonical element in the respective model.

---

### Specification Cost

- **FR-007**: Specification Cost MUST be derived exclusively from the Canonical Specification Model.

- **FR-008**: Specification Activities MAY contribute configurable weights according to their activity type.

- **FR-009**: Decisions, Assumptions, Constraints, Risks, Open Questions, Acceptance Criteria and Glossary Terms MAY contribute configurable weights.

---

### Code Generation Cost

- **FR-010**: Code Generation Cost MUST be derived exclusively from the Canonical Functional Model.

- **FR-011**: Functional Processes, Business Rules, Operations, Data Groups, Relationships and Actors MAY contribute configurable weights.

---

### Calibration

- **FR-012**: All weighting factors MUST be externally configurable via YAML files.

- **FR-013**: Built-in default calibration MUST be provided.

- **FR-014**: Organization-specific calibration MUST override defaults through Rule Packs.

- **FR-015**: Calibration MUST NOT require code changes.

---

### Explainability

- **FR-016**: Every Token Points contribution MUST be individually reported.

- **FR-017**: Every contribution MUST preserve evidence references.

- **FR-018**: The engine MUST generate a measurement breakdown showing:
  - contributing canonical element
  - applied weight
  - partial score
  - cumulative score

---

### Determinism

- **FR-019**: Equal canonical models MUST always produce identical Token Points measurements.

---

### Events

- **FR-020**: The engine MUST emit a `TokenPointsMeasured` pipeline event.

---

# Key Entities _(include if feature involves data)_

## TokenPointsMeasurement

Represents the complete Token Points result. Identified by pipeline run ID.

Contains:

- total score
- Specification Cost
- Code Generation Cost
- calibration version
- measurement metadata
- evidence references

---

## SpecificationCost

Represents the estimated computational effort required to create, clarify, refine and validate the specification.

Derived exclusively from the CSM.

Contains:
- **total**: Aggregate specification cost score
- **contributions**: List of TokenContribution elements

---

## CodeGenerationCost

Represents the estimated computational effort required to generate software artifacts from the specification.

Derived exclusively from the CFM.

Contains:
- **total**: Aggregate code generation cost score
- **contributions**: List of TokenContribution elements

---

## TokenContribution

Represents an individual contribution to the Token Points score.

Contains:

- canonical element
- canonical model (CFM or CSM)
- applied weight
- partial score
- evidence reference

---

## CalibrationProfile

Defines all configurable weights used by the engine. Serialized as YAML with hierarchical structure.

Top-level sections:
- **specification_cost**: per-type weights for CSM entities (activities, decisions, assumptions, constraints, risks, open questions, acceptance criteria, glossary terms)
- **code_generation_cost**: per-type weights for CFM entities (functional_processes, business_rules, operations, data_groups, relationships, actors)

Supports:

- built-in defaults
- organization overrides
- versioning

---

# Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Measuring the same CFM and CSM twice produces identical Token Points results.

- **SC-002**: 100% of Token Points contributions are traceable to canonical elements.

- **SC-003**: Default calibration can be completely replaced without modifying engine code.

- **SC-004**: Measuring repositories from different specification frameworks produces equivalent Token Points when their canonical models are equivalent.

- **SC-005**: A measurement report includes a complete explainability breakdown for every score contribution.

- **SC-006**: The engine measures a repository containing 500 canonical elements in under 2 seconds on a standard development machine.

---

# Assumptions

- Token Points are an **engineering estimation metric**, not a measurement of actual LLM token consumption.
- Actual token usage varies across LLM providers, models, prompting strategies, and implementation workflows.
- Calibration values are expected to evolve as organizations collect historical execution data.
- The initial calibration is heuristic and deterministic, while future versions may provide organization-specific calibration profiles derived from historical telemetry.
- The engine intentionally estimates **relative computational effort**, enabling backlog prioritization, AI budget forecasting, sprint planning, Kanban replenishment, and PI/IP Planning without depending on a specific LLM vendor or tokenizer.
- Token Points are independent of pricing models (USD/token, credits, subscriptions, etc.), allowing organizations to translate the measurement into monetary cost using their own conversion factors.
