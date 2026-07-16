# Feature Specification: Explain Measurement

**Feature Branch**: `016-explain-measurement`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "F15 Explain Measurement"

## User Scenarios & Testing

### User Story 1 - Explain a measurement result (Priority: P1)

A user has executed a measurement pipeline on a specification and received metrics such as functional size or complexity counts. They want to understand where those numbers came from — which specification elements contributed, what evidence supports each value, and which rules were applied. They request an explanation for a specific metric and receive a clear, structured breakdown.

**Why this priority**: This is the core flow. Without the ability to explain a single measurement result, the feature delivers no value. It directly satisfies the "Explainability by Design" constitutional principle (VI).

**Independent Test**: Can be fully tested by executing a measurement on a known specification, requesting an explanation for a specific metric, and verifying the explanation references the expected specification elements, evidence fragments, and applied rules.

**Acceptance Scenarios**:

1. **Given** a measurement has completed on a specification with at least one identified function, **When** the user requests an explanation for the functional size metric, **Then** the explanation lists each identified function, its complexity classification, and the specification section that defines it
2. **Given** a measurement result that had counting rules applied (e.g., weighting rules from a Rule Pack), **When** the user requests an explanation, **Then** the explanation identifies which rules were applied and how they affected the final value
3. **Given** a measurement result with no applicable rules, **When** the user requests an explanation, **Then** the explanation shows raw counts with a note that no Rule Pack rules were applied

---

### User Story 2 - Trace a metric to its source evidence (Priority: P2)

A reviewer wants to verify that a measurement is accurate by tracing each counted element back to the original specification text. They navigate from a metric value through the evidence graph to see the exact specification fragments that contributed.

**Why this priority**: Traceability is the foundation of trust in measurements (Principle V - Evidence First). It enables auditing and review, but the basic explain flow in P1 already provides high-level attribution.

**Independent Test**: Can be tested by providing a specification with known content, running measurement, tracing a single count to its source evidence, and verifying the evidence text matches the original specification.

**Acceptance Scenarios**:

1. **Given** a metric that counts a specific element (e.g., "3 functions identified"), **When** the user drills into that metric, **Then** each counted element shows a direct citation of the specification section and text fragment that caused it to be counted
2. **Given** an element that was identified across multiple specification sections, **When** the user views its evidence trail, **Then** each contributing section is listed with the relevant excerpt
3. **Given** an element with no direct evidence (orphan count), **When** the user attempts to trace it, **Then** the system reports the count with a "no evidence reference" warning

---

### User Story 3 - Compare explanations across measurement runs (Priority: P3)

A maintainer has made changes to a specification and wants to understand how the measurement results differ from the previous version. They request a comparison of two explanations side by side, highlighting what changed and why.

**Why this priority**: Comparison aids governance and review workflows but is not essential for the core explainability use case. It builds on the P1 and P2 capabilities.

**Independent Test**: Can be tested by providing two versions of the same specification with one known difference, running measurement on both, requesting a comparison explanation, and verifying the output highlights the expected difference.

**Acceptance Scenarios**:

1. **Given** two measurement results from different versions of the same specification, **When** the user requests a comparison, **Then** the system shows which metrics changed and the specification elements responsible for each change
2. **Given** two measurement results where no values changed, **When** the user requests a comparison, **Then** the system reports "No differences found" with confirmation timestamps
3. **Given** a comparison request where one measurement result is unavailable, **When** the user requests the comparison, **Then** the system reports the missing result without error

---

### Edge Cases

- What happens when the evidence graph is empty or unavailable? — The explanation should indicate that evidence is missing and show the measurement values with a warning
- How does the system handle incomplete explanations (e.g., rules applied but rule definitions missing)? — Report known information and flag missing rule definitions as gaps
- What happens when the user requests an explanation for a metric that doesn't exist? — Return a clear "metric not found" message
- How does the system behave when the specification has been deleted since measurement? — Explanation still shows the evidence that was captured at measurement time, with a note that the source is no longer available

## Constitution Check

**Engaged Principles**: Explainability by Design (VI), Evidence First (V), Rule Externalization (IX)

**Compliance Notes**:
- **Explainability by Design (VI)**: This feature is the direct implementation of Principle VI. Every measurement must be explainable, and explanations must be generated automatically from the evidence graph.
- **Evidence First (V)**: Explanations MUST reference the originating evidence for each counted element. The evidence graph is the source of truth for all traceability.
- **Rule Externalization (IX)**: Explanations MUST identify which Rule Pack rules were applied during measurement and how they affected the results.
- **Specification First (I)**: Explanations reference specification sections and fragments, not implementation code.
- **Layer Independence (XIV)**: The explanation capability must consume the Canonical Functional Model and Evidence Graph outputs without depending on the internal details of the Measurement Engine.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide an explanation for any completed measurement result upon request
- **FR-002**: System MUST identify which specification elements (functions, operations, entities) contributed to each metric value in the explanation
- **FR-003**: System MUST reference the specific specification sections and text fragments that caused each element to be counted
- **FR-004**: System MUST list all Rule Pack rules that were applied during measurement and describe their effect on the results
- **FR-005**: System MUST support drilling down from a metric value to view the individual evidence items that produced it
- **FR-006**: System MUST support comparison of explanations between two measurement runs, highlighting changes in metrics and their contributing elements
- **FR-007**: System MUST handle missing or incomplete evidence gracefully — report available information and flag gaps
- **FR-008**: System MUST report a clear "metric not found" error when the requested metric does not exist in the measurement results
- **FR-009**: System MUST preserve measurement-time evidence so explanations remain available even if the source specification is later modified or deleted
- **FR-010**: System MUST produce explanations in a structured, machine-readable format suitable for UI rendering and automated consumption

### Key Entities

- **MeasurementExplanation**: The full explanation output for a single measurement. Contains per-metric explanations, applied rule references, and overall evidence summary.
- **MetricExplanation**: Explanation for a single metric value (e.g., "functional size = 12"). Lists each contributing element, its evidence, and the rules that affected it.
- **EvidenceReference**: A pointer to the specific specification section and text fragment that justifies a counted element. Includes document ID, section path, and excerpt.
- **AppliedRule**: A record of a Rule Pack rule that was applied during measurement. Includes rule name, description of effect, and which elements it impacted.
- **ExplanationComparison**: A comparison between two MeasurementExplanation instances. Shows added, removed, and modified metrics with their evidence differences.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can request and receive an explanation for any single metric in under 2 seconds for specifications up to 500 identified elements
- **SC-002**: Each explanation for a metric includes evidence references for 100% of the elements that contributed to that metric
- **SC-003**: Users can successfully trace any counted element back to its original specification text in 3 or fewer navigation steps
- **SC-004**: Comparison explanations correctly identify 100% of changes between two measurement runs of the same specification with known differences
- **SC-005**: 90% of users can understand the explanation output without referring to external documentation (measured through user testing)

## Assumptions

- The Evidence Graph is populated and available at explanation time (it is the primary source for traceability)
- Rule Packs record which rules were applied during measurement and their per-element effects
- Each specification element in the Canonical Functional Model maintains provenance references back to the Evidence Graph
- The Measurement Engine preserves intermediate computation details (not just final values) to enable granular explanations
- Explanations are consumed via CLI, MCP, and API interfaces (consistent with Principle X - AI-Friendly by Design)
- The Canonical Functional Model is the authoritative source for what elements were counted and their classification
- Explanation files are persisted to `.specmetrics/explanations/{run_id}.json` by default
