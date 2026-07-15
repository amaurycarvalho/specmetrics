# Feature Specification: Measurement Engine Plugin — APF

**Feature Branch**: `008-measurement-engine-apf`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "F07"

---

## User Scenarios & Testing

### User Story 1 — Automated APF Measurement (Priority: P1)

A quality engineer runs `specmetrics measure` on a project and receives a complete IFPUG/APF function point count calculated automatically from the specification documents via the Canonical Functional Model. The measurement includes both Data Functions (ILF, EIF) and Transactional Functions (EI, EO, EQ) with no manual counting effort.

**Why this priority**: Automated function point counting is the core value proposition of SpecMetrics. Without the Measurement Engine, the platform cannot produce functional size measurements — its primary output.

**Independent Test**: Can be fully tested by providing a Canonical Functional Model containing known actors, functional processes, and data groups, running the measurement, and verifying the resulting counts match expected APF values.

**Acceptance Scenarios**:

1. **Given** a valid Canonical Functional Model with identified data groups and functional processes, **When** the Measurement Engine runs, **Then** it produces an APF count with ILF, EIF, EI, EO, and EQ contributions
2. **Given** a CFM with 5 Internal Logical Files and 10 External Inputs, **When** measured, **Then** the output reports 5 ILFs and 10 EIs with correct complexity ratings
3. **Given** an empty CFM (no functions identified), **When** measured, **Then** the engine returns a zero count without errors

---

### User Story 2 — Explainable Measurement Results (Priority: P1)

A quality engineer inspects a function point count and wants to understand why each function was counted at its specific complexity level. The system provides a full trace showing which CFM elements contributed to each measured function, which rules were applied, and the individual contribution to the final count.

**Why this priority**: Trust in automated measurement requires transparency. Without explainability, users cannot validate or audit the results.

**Independent Test**: Can be tested by measuring a CFM and verifying that the output includes evidence references for each measured function, linking back to specific CFM elements.

**Acceptance Scenarios**:

1. **Given** a measurement result, **When** the user requests the explanation for a specific measured function, **Then** the system provides the originating CFM element, the counting rule applied, and the contribution to the total
2. **Given** a measurement result with 15 measured functions, **When** inspected, **Then** every function includes traceable evidence references
3. **Given** a measurement with Rule Pack adjustments, **When** explained, **Then** the report includes which rules modified the count and how

---

### User Story 3 — Rule Pack Integration (Priority: P1)

A team lead applies an organizational Rule Pack that defines custom counting policies (e.g., excluding certain interface types, adjusting complexity thresholds). The Measurement Engine applies these rules before producing the final measurement, and the adjustments are transparently documented.

**Why this priority**: Rule Externalization (Principle IX) requires the Measurement Engine to consume external policies. Without this integration, all counting rules would be hardcoded.

**Independent Test**: Can be tested by providing a CFM with and without a Rule Pack that excludes a known function type, and verifying the counts differ by the expected amount.

**Acceptance Scenarios**:

1. **Given** a CFM and a Rule Pack that excludes External Inquiries from counting, **When** measured, **Then** the result excludes EQ contributions
2. **Given** a CFM and a Rule Pack that adjusts complexity thresholds, **When** measured, **Then** the complexity ratings reflect the custom thresholds
3. **Given** an empty Rule Pack (no custom policies), **When** measured, **Then** the engine applies default IFPUG counting rules

---

### User Story 4 — Plugin Discovery and Pipeline Integration (Priority: P2)

The Measurement Engine is automatically discovered by the Plugin Registry at startup and loaded into the Pipeline Engine without manual configuration. The Pipeline Engine invokes the Measurement Engine at the correct stage after the Rule Pack Engine (F09) has applied organizational policies.

**Why this priority**: Plugin-Oriented Architecture (Principle VIII) requires the engine to be a discoverable plugin. However, manual registration is acceptable as a fallback for the first iteration.

**Independent Test**: Can be tested by packaging the Measurement Engine as a plugin, starting the system, and verifying it appears in the Plugin Registry.

**Acceptance Scenarios**:

1. **Given** the Measurement Engine is installed as a Python package, **When** the system starts, **Then** it is discovered and registered by the Plugin Registry
2. **Given** the Pipeline Engine is executing a measurement pipeline, **When** the measurement stage is reached, **Then** the Measurement Engine is invoked with the CFM and applied Rule Packs
3. **Given** an invalid or corrupted Measurement Engine plugin, **When** loaded, **Then** the system reports the error and continues without crashing

---

### Edge Cases

- What happens when the CFM contains no recognizable functions? The engine returns a zero count with a clear informational message.
- What happens when the CFM references data groups that don't exist? The engine skips unresolved references and includes them in a warnings report.
- What happens when a Rule Pack defines contradictory policies? The last applicable rule wins and the conflict is logged.
- What happens when required Rule Pack dependencies are missing? The engine uses default IFPUG rules and logs the missing dependency.
- How does the engine handle extremely large CFMs (1000+ functions)? Measurement is batched internally; total processing time scales linearly with function count.

---

## Constitution Check

**Engaged Principles**:

- **IV (LLM-Assisted, Deterministic Results)** — The Measurement Engine is purely deterministic. All counting rules execute without LLM involvement. Reproducibility is guaranteed: same CFM + same rules = same result.
- **VI (Explainability by Design)** — Every measured function preserves its evidence trail. Users can inspect why each function was counted and at which complexity.
- **IX (Rule Externalization)** — Counting policies are applied from external Rule Packs, not hardcoded into the engine. Organization-specific rules are loaded at measurement time.
- **VII (Canonical Representation)** — The engine consumes only the Canonical Functional Model. No framework-specific concepts leak into the measurement logic.
- **VIII (Plugin-Oriented)** — The Measurement Engine is a discoverable plugin. It communicates through the Kernel via published contracts.

**Compliance Notes**: The engine satisfies Principle IV by executing explicit counting rules deterministically. Principle VI is satisfied by preserving evidence references for every measured function. Principle IX is satisfied by accepting Rule Packs as external inputs rather than embedding counting logic. Principle VII is satisfied by consuming only CFM elements. Principle VIII is satisfied by implementing the published Measurement Engine plugin interface.

---

## Requirements

### Functional Requirements

- **FR-001**: The Measurement Engine MUST consume the Canonical Functional Model as its sole semantic input — it MUST NOT access specification documents, evidence graphs, or framework-specific artifacts directly
- **FR-002**: The Measurement Engine MUST implement IFPUG/APF counting rules for all five function types: Internal Logical Files (ILF), External Interface Files (EIF), External Inputs (EI), External Outputs (EO), and External Inquiries (EQ)
- **FR-003**: Each function type MUST be classified according to its complexity (Low, Average, High) based on Data Element Types (DETs) and Record Element Types (RETs) for data functions, and DETs and File Types Referenced (FTRs) for transactional functions
- **FR-004**: The Measurement Engine MUST apply organizational Rule Packs before producing final measurements, overriding default IFPUG rules where the Rule Pack specifies custom behavior
- **FR-005**: When no Rule Pack is provided, the Measurement Engine MUST use standard IFPUG counting rules as defaults
- **FR-006**: The Measurement Engine MUST produce deterministic results — identical CFM input with identical Rule Packs MUST produce identical output on every execution
- **FR-007**: Every measured function MUST preserve references (evidence trail) to the CFM elements that originated it, enabling downstream explainability
- **FR-008**: The Measurement Engine MUST NOT perform semantic extraction, LLM inference, or any non-deterministic operations
- **FR-009**: The Measurement Engine MUST be implemented as a discoverable plugin via Python Entry Points under the `specmetrics.plugins.measurement` group
- **FR-010**: The Measurement Engine MUST produce machine-readable measurement output suitable for consumption by Export Layer plugins (F10) and Publisher plugins (F11)
- **FR-011**: When the CFM is empty or contains no recognizable functions, the Measurement Engine MUST return a zero-count result without errors
- **FR-012**: When the CFM contains references to unresolved or missing elements, the Measurement Engine MUST report warnings for each unresolved reference and continue measurement with available elements
- **FR-013**: The Measurement Engine MUST report clear error messages when required inputs (CFM) are missing or in an invalid format

### Key Entities

- **APF Measurement Result**: The complete output of the measurement process — contains total function point count, breakdown by function type, complexity distribution, and evidence references
- **Measured Function**: A single function point classified as ILF, EIF, EI, EO, or EQ with its complexity rating, DET/RET/FTR counts, and evidence trail back to the originating CFM element
- **Function Type Counter**: The deterministic logic that scans the CFM, identifies candidate functions, and classifies them by type and complexity
- **Rule Pack Applicator**: The component that reads organizational Rule Packs and applies custom counting policies, complexity thresholds, and exclusions before finalizing measurements
- **Complexity Matrix**: The IFPUG-standard grid that maps DET/RET counts (data functions) or DET/FTR counts (transactional functions) to Low/Average/High complexity ratings, optionally overridable by Rule Packs

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A Canonical Functional Model containing 10 data groups and 15 functional processes produces a complete APF count within 5 seconds on standard hardware
- **SC-002**: Every measured function in the output includes traceable evidence references to specific CFM elements — 100% of functions must have non-empty evidence trails
- **SC-003**: Applying a Rule Pack that excludes External Inquiries from counting reduces the total function count by exactly the number of EQs identified in the CFM, without modifying the CFM itself
- **SC-004**: Running the same measurement twice on identical CFM and Rule Pack inputs produces byte-identical results
- **SC-005**: The Measurement Engine is discovered and loaded by the Plugin Registry without manual configuration when packaged as a Python plugin
- **SC-006**: Invalid or incomplete CFM inputs produce descriptive error messages that identify the specific validation failure — no silent incorrect measurements are produced
- **SC-007**: The Measurement Engine correctly processes CFMs with 500+ functions without errors or performance degradation exceeding linear scaling expectations

---

## Assumptions

- The Canonical Functional Model (F06) is fully implemented and provides a stable, complete representation of identified functions, data groups, actors, and operations
- The Rule Pack Engine (F09) is available as a dependency — however, the Measurement Engine defines the Rule Pack interface contract such that minimal Rule Pack support (empty/default rules) enables full measurement
- APF counting follows IFPUG CPM 4.3 as the default methodology; organizational Rule Packs may deviate from this baseline
- Value Adjustment Factor (VAF) and General System Characteristics (GSC) are handled through Rule Packs rather than hardcoded in the engine — the engine produces Unadjusted Function Points (UFP) by default, with VAF applied if the Rule Pack provides GSC ratings
- The Measurement Engine runs as a single stage in the event-driven pipeline — it receives the CFM after Rule Pack (F09) processing
- Multiple measurement methodologies (e.g., SPF, SNAP) are out of scope for this feature — each methodology is a separate plugin
- Export formatting (JSON, CSV, XML) is handled by F10, not by the Measurement Engine — the engine produces a structured internal representation
