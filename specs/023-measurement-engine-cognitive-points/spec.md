# Feature Specification: Measurement Engine Plugin — Cognitive Points

**Feature Branch**: `023-measurement-engine-cognitive-points`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "Cognitive Points"

---

# User Scenarios & Testing _(mandatory)_

## User Story 1 - Estimate human cognitive effort for specification review and delivery validation (Priority: P1)

A technical leader executes the SpecMetrics measurement pipeline and receives a Cognitive Points measurement representing the estimated human cognitive effort required to review, validate, and approve both the specification and the implementation generated from it. The measurement reflects the expected Human-in-the-Loop (HITL) effort rather than implementation effort.

**Why this priority**

As AI automates software construction, the primary human effort shifts from coding to specification refinement, review, validation, and quality assurance. Engineering teams require a deterministic metric to estimate this cognitive workload for planning and capacity management.

**Independent Test**

Execute the pipeline using a known specification containing varying levels of specification maturity and functional complexity. Verify that Cognitive Points are deterministically calculated from the Canonical Functional Model (CFM), Canonical Specification Model (CSM), and configured cognitive calibration rules.

### Acceptance Scenarios

1. **Given** a specification with multiple clarification activities, complex business rules, and extensive decision logic, **When** the Cognitive Points engine executes, **Then** it produces a deterministic Cognitive Points measurement together with a complete explanation of the contributing factors.

2. **Given** identical canonical models, **When** Cognitive Points are measured multiple times, **Then** identical results are produced.

3. **Given** equivalent specifications authored in OpenSpec and SpecKit, **When** Cognitive Points are calculated, **Then** the resulting measurement is framework-independent.

---

## User Story 2 - Understand the sources of cognitive complexity (Priority: P1)

A specification reviewer analyzes the Cognitive Points report to identify which aspects of the specification require the greatest human attention during review and validation.

**Why this priority**

Cognitive effort must be explainable. Teams need to understand whether review effort originates from domain complexity, specification maturity, ambiguity, or functional behavior.

**Independent Test**

Inspect the generated report and verify that every Cognitive Points contribution references the originating canonical elements together with the applied cognitive level and weighting.

### Acceptance Scenarios

1. **Given** a completed measurement, **When** the reviewer inspects the report, **Then** every Cognitive Points contribution identifies the originating canonical element and cognitive classification.

2. **Given** a specification containing numerous unresolved assumptions and open questions, **When** Cognitive Points are calculated, **Then** these elements contribute to the overall cognitive effort.

3. **Given** configured cognitive calibration rules, **When** the measurement executes, **Then** every applied calibration value is included in the explainability report.

---

## User Story 3 - Support delivery planning and team capacity forecasting (Priority: P2)

A Scrum Master, Kanban Flow Manager, or Product Manager aggregates Cognitive Points across a backlog to estimate the human review capacity required for a Sprint, Kanban replenishment, Release Planning, or PI/IP Planning.

**Why this priority**

AI-assisted delivery shifts team capacity constraints toward human validation activities. Cognitive Points provide a planning metric for estimating review workload independently of implementation effort.

**Independent Test**

Aggregate Cognitive Points across multiple specifications and verify deterministic project-level totals.

### Acceptance Scenarios

1. **Given** several measured specifications, **When** Cognitive Points are aggregated, **Then** the project total equals the sum of the individual measurements.

2. **Given** updated cognitive calibration profiles, **When** measurements are recalculated, **Then** the resulting Cognitive Points reflect the revised calibration.

---

# Edge Cases

- What happens when no Specification Activities exist? Specification Review Effort is zero while Functional Validation Effort may still be calculated.
- What happens when the CFM is empty? Cognitive Points are derived solely from specification-related cognitive work.
- What happens when no cognitive calibration profile is configured? The engine loads the built-in default calibration.
- What happens when canonical elements cannot be mapped to a cognitive level? They receive the configured default cognitive weight and are reported in the measurement metadata.
- What happens when a specification is functionally simple but contains numerous unresolved questions? The specification maturity component increases the Cognitive Points score even if the functional complexity remains low.

---

# Constitution Check _(mandatory)_

**Engaged Principles**: VII (Canonical Representation), VIII (Plugin-Oriented Architecture), V (Evidence First), XV (Deterministic Measurement)

**Compliance Notes**

- Consumes only canonical models (CFM and CSM).
- Produces deterministic measurements.
- Preserves complete evidence traceability.
- Externalizes organizational calibration through Rule Packs.

---

# Requirements _(mandatory)_

## Functional Requirements

### Measurement Engine

- **FR-001**: The Cognitive Points engine MUST be implemented as a Measurement Engine plugin.

- **FR-002**: The engine MUST consume the Canonical Functional Model (CFM) and the Canonical Specification Model (CSM).

- **FR-003**: The engine MUST produce a deterministic Cognitive Points measurement.

---

### Measurement Model

- **FR-004**: Cognitive Points MUST represent the estimated human cognitive effort required to review, validate, and approve an AI-assisted software delivery.

- **FR-005**: The measurement MUST be composed of two independent components:
  - Specification Review Effort
  - Functional Validation Effort

- **FR-006**: The engine MUST calculate:

```text
Cognitive Points =
Specification Review Effort
+
Functional Validation Effort
```

---

### Specification Review Effort

- **FR-007**: Specification Review Effort MUST be derived exclusively from the Canonical Specification Model.

- **FR-008**: Specification Activities MAY contribute configurable cognitive weights according to their activity type.

- **FR-009**: Decisions, Assumptions, Constraints, Risks, Open Questions, Acceptance Criteria and Glossary Terms MAY contribute configurable cognitive weights.

---

### Functional Validation Effort

- **FR-010**: Functional Validation Effort MUST be derived exclusively from the Canonical Functional Model.

- **FR-011**: Functional Processes, Business Rules, Operations, Data Groups, Relationships and Actors MAY contribute configurable cognitive weights.

---

### Bloom Cognitive Model

- **FR-012**: Every canonical element contributing to Cognitive Points MUST be classified into a configurable Bloom-based cognitive level.

- **FR-013**: The engine MUST support organization-specific mappings between canonical elements and Bloom cognitive levels.

- **FR-014**: The default cognitive taxonomy SHALL include the following levels:
  - Remember
  - Understand
  - Apply
  - Analyze
  - Evaluate
  - Create

- **FR-015**: Each Bloom level MUST have an externally configurable cognitive weight.

---

### Fibonacci Normalization

- **FR-016**: The final Cognitive Points measurement MUST be normalized to a modified Fibonacci scale.

- **FR-017**: The normalization table MUST be externally configurable.

- **FR-018**: Organizations MAY replace the default normalization profile without modifying engine code.

---

### Calibration

- **FR-019**: All cognitive weights, Bloom mappings, normalization tables, penalties and adjustment factors MUST be externally configurable.

- **FR-020**: The engine MUST provide a built-in default calibration profile.

---

### Explainability

- **FR-021**: Every Cognitive Points contribution MUST be individually reported.

- **FR-022**: Every contribution MUST preserve complete evidence references.

- **FR-023**: The measurement report MUST include:
  - canonical element
  - originating canonical model (CFM or CSM)
  - Bloom cognitive level
  - applied cognitive weight
  - partial score
  - normalization result
  - cumulative score

---

### Determinism

- **FR-024**: Equal canonical models MUST always produce identical Cognitive Points measurements.

---

### Events

- **FR-025**: The engine MUST emit a `CognitivePointsMeasured` pipeline event.

---

# Key Entities _(include if feature involves data)_

## CognitivePointsMeasurement

Represents the complete Cognitive Points result.

Contains:

- total Cognitive Points
- Specification Review Effort
- Functional Validation Effort
- normalized score
- calibration profile
- measurement metadata
- evidence references

---

## SpecificationReviewEffort

Represents the estimated human cognitive effort required to analyze, refine, review and validate the specification.

Derived exclusively from the CSM.

---

## FunctionalValidationEffort

Represents the estimated human cognitive effort required to review and validate the generated implementation.

Derived exclusively from the CFM.

---

## CognitiveContribution

Represents an individual contribution to the Cognitive Points measurement.

Contains:

- canonical element
- canonical model
- Bloom level
- cognitive weight
- partial score
- normalized contribution
- evidence reference

---

## BloomClassification

Represents the cognitive classification assigned to a canonical element.

Contains:

- Bloom level
- rationale
- configured weight

---

## FibonacciNormalizationProfile

Defines how the accumulated cognitive score is converted into the organization's modified Fibonacci scale.

Supports:

- configurable thresholds
- configurable output values
- versioning

---

## CognitiveCalibrationProfile

Defines all configurable parameters used by the Cognitive Points engine, including:

- Bloom mappings
- cognitive weights
- normalization profile
- penalties
- adjustment factors

Supports:

- built-in defaults
- organization overrides
- versioning

---

# Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Measuring identical CFM and CSM models twice produces identical Cognitive Points measurements.

- **SC-002**: 100% of Cognitive Points contributions are traceable to canonical elements.

- **SC-003**: Default Bloom mappings, cognitive weights and Fibonacci normalization can be completely replaced without modifying engine code.

- **SC-004**: Equivalent canonical models generated from different specification frameworks produce identical Cognitive Points measurements.

- **SC-005**: Every measurement report contains a complete explainability breakdown, including Bloom classification, applied weights and normalization.

- **SC-006**: The engine measures repositories containing 500 canonical elements in under 2 seconds on a standard development machine.

---

# Assumptions

- Cognitive Points are an **engineering estimation metric**, not a measurement of elapsed review time or developer productivity.
- The metric estimates the expected Human-in-the-Loop (HITL) effort required to achieve an implementation-ready and production-ready software delivery.
- Bloom's Taxonomy provides the conceptual foundation for estimating cognitive complexity but is adapted through configurable organizational calibration.
- The modified Fibonacci scale serves as a normalization mechanism for planning and forecasting rather than an absolute measurement of effort.
- Calibration values are expected to evolve as organizations collect historical review metrics, delivery lead time, approval cycles, defect escape rates, and implementation telemetry.
- Cognitive Points are intended to support Sprint Planning, Kanban replenishment, PI/IP Planning, review capacity forecasting, and engineering governance in AI-assisted software development, while remaining independent of any specific agile framework or estimation methodology.
