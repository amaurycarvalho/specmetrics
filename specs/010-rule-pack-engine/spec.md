# Feature Specification: Rule Pack Engine

**Feature Branch**: `010-rule-pack-engine`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "F09"

## User Scenarios & Testing

### User Story 1 — Define and Load an Organizational Rule Pack (Priority: P1)

A team lead defines custom counting policies for their organization by writing a Rule Pack file. The Rule Pack Engine loads this file and makes the policies available to the measurement pipeline, without requiring any code changes or platform modifications.

**Why this priority**: Rule Externalization (Principle IX) is a core architectural requirement. Without Rule Pack loading, all policies would be hardcoded, violating the architecture.

**Independent Test**: Can be fully tested by creating a Rule Pack file, loading it through the engine, and verifying the engine reports the loaded rules with their expected values.

**Acceptance Scenarios**:

1. **Given** a valid Rule Pack file in the project's rules directory, **When** the pipeline reaches the Rule Pack Engine stage, **Then** the engine loads all rules from the file and reports them as active
2. **Given** no Rule Pack files exist in the project, **When** the pipeline reaches the Rule Pack Engine stage, **Then** the engine reports no active rules and passes the CFM through unmodified
3. **Given** an invalid Rule Pack file with syntax errors, **When** loaded, **Then** the engine reports a descriptive error identifying the file, line, and nature of the syntax issue

---

### User Story 2 — Apply Counting Rule Exclusions (Priority: P1)

A quality engineer configures a Rule Pack to exclude External Inquiries from counting for their project. The Rule Pack Engine applies this exclusion to the Canonical Functional Model before the Measurement Engine runs, and the final measurement excludes EQ contributions.

**Why this priority**: Rule application is the primary function of the engine. Together with Story 1, this forms the minimum viable capability.

**Independent Test**: Can be tested by providing a CFM with known EQs and a Rule Pack that excludes EQs, then verifying the applied output marks EQs as excluded.

**Acceptance Scenarios**:

1. **Given** a CFM containing 5 External Inquiries and a Rule Pack with `exclude: [EQ]`, **When** the engine applies the Rule Pack, **Then** the output CFM marks all 5 EQs as excluded from counting
2. **Given** a CFM and a Rule Pack with no exclusions, **When** applied, **Then** all functions remain eligible for counting
3. **Given** a Rule Pack that excludes a function type not present in the CFM, **When** applied, **Then** the engine reports the exclusion rule as active with zero affected functions

---

### User Story 3 — Custom Complexity Thresholds (Priority: P2)

A team lead adjusts complexity thresholds for their domain (e.g., lowering the threshold for High complexity on External Inputs). The Rule Pack Engine applies these thresholds to the CFM, and the Measurement Engine uses the adjusted complexity ratings.

**Why this priority**: Custom complexity thresholds enable domain-specific measurement accuracy, extending beyond default IFPUG rules.

**Independent Test**: Can be tested by providing a CFM and a Rule Pack with modified thresholds, verifying the output reflects the custom thresholds rather than defaults.

**Acceptance Scenarios**:

1. **Given** a CFM and a Rule Pack defining custom DET/FTR thresholds for EI complexity, **When** the engine applies the Rule Pack, **Then** the affected functions are reclassified with the custom complexity ratings
2. **Given** a Rule Pack that modifies thresholds for only one function type (e.g., EI), **When** applied, **Then** all other function types retain their default complexity ratings
3. **Given** invalid threshold values (e.g., negative DET counts), **When** the Rule Pack is loaded, **Then** the engine reports a validation error and does not apply the invalid rule

---

### User Story 4 — Trace Applied Rules (Priority: P2)

A quality engineer inspects measurement results and wants to see exactly which Rule Pack rules were applied to each function. The Rule Pack Engine annotates the CFM with applied rule references, enabling downstream explainability.

**Why this priority**: Principle VI (Explainability by Design) requires traceability. Without rule annotations, users cannot distinguish default behavior from policy-driven adjustments.

**Independent Test**: Can be tested by applying a Rule Pack with known exclusions and verifying the output CFM contains rule references for each applied exclusion.

**Acceptance Scenarios**:

1. **Given** a CFM and a Rule Pack that excludes EQs, **When** the engine applies the Rule Pack, **Then** each excluded function in the output includes a reference to the specific rule that excluded it
2. **Given** a Rule Pack with multiple rules affecting the same function, **When** applied, **Then** the function's annotations include all applicable rule references
3. **Given** no Rule Pack is loaded, **When** the engine runs, **Then** the output CFM contains a note that default IFPUG rules were used

---

### Edge Cases

- What happens when multiple Rule Packs define conflicting rules for the same function type? The last loaded Rule Pack takes precedence and the conflict is logged as a warning.
- What happens when a Rule Pack references a function type or attribute that doesn't exist in the CFM? The engine logs the unused rule as informational and continues.
- What happens when a Rule Pack file is modified between pipeline executions? The engine reloads all Rule Pack files at the start of each pipeline execution; no caching of Rule Pack state across executions.
- How does the engine handle circular rule dependencies? Rule Packs are declarative, not programmatic — no dependency resolution is required. Each rule is independently evaluated.
- What happens when a Rule Pack contains a rule that cannot be applied (e.g., references an invalid complexity matrix cell)? The engine skips the rule, logs the error, and continues with remaining rules.

## Constitution Check

**Engaged Principles**:

- **IX (Rule Externalization)** — This feature is the direct implementation of Principle IX. All counting policies are externalized as Rule Packs rather than embedded in platform code.
- **VI (Explainability by Design)** — The engine annotates every applied rule on the affected functions, preserving evidence of what was modified and why.
- **VII (Canonical Representation)** — The engine consumes and produces the Canonical Functional Model. Rule Packs modify CFM attributes without introducing framework-specific concepts.
- **IV (LLM-Assisted, Deterministic Results)** — Rule application is purely deterministic. Identical CFM + identical Rule Packs produce identical output.
- **XIV (Layer Independence)** — The Rule Pack Engine depends only on the CFM contract. Changes to Rule Pack format or loading do not affect upstream extraction or downstream measurement.
- **VIII (Plugin-Oriented)** — Rule Packs are external files, not plugins. However, the Rule Pack Engine itself may be a plugin implementing the published pipeline stage contract.

**Compliance Notes**: Principle IX is satisfied by design — Rule Packs are external files loaded at pipeline execution time, not compiled code. Principle VI is satisfied by preserving applied rule references in the output CFM. Principle VII is satisfied because all modifications target CFM attributes, not framework-specific artifacts. Principle IV is satisfied because rule application follows explicit, deterministic logic. Principle XIV is satisfied because the engine communicates only through the CFM contract. Principle VIII is satisfied because the engine is a pipeline stage loaded through the Plugin Registry.

## Requirements

### Functional Requirements

- **FR-001**: The Rule Pack Engine MUST load Rule Packs from a well-defined project directory (`.specify/rules/` by default) at the start of each pipeline execution
- **FR-002**: Rule Packs MUST be authored as external files using a structured format (YAML) — no code, scripting, or programmatic logic in Rule Packs
- **FR-003**: The Rule Pack Engine MUST support exclusion rules that mark specific function types (ILF, EIF, EI, EO, EQ) as excluded from counting
- **FR-004**: The Rule Pack Engine MUST support complexity threshold overrides that customize the DET/RET (data functions) and DET/FTR (transactional functions) boundaries for Low/Average/High classification
- **FR-005**: When no Rule Pack files exist, the Rule Pack Engine MUST pass the CFM through unmodified, applying no custom policies
- **FR-006**: When multiple Rule Packs define conflicting rules, the last loaded Rule Pack MUST take precedence, and the conflict MUST be logged as a warning
- **FR-007**: The Rule Pack Engine MUST validate all loaded Rule Packs and report descriptive errors for invalid syntax, unknown function types, and out-of-range threshold values
- **FR-008**: The Rule Pack Engine MUST annotate the output CFM with references to every applied rule, linking each modification to the specific rule and Rule Pack file that caused it
- **FR-009**: The Rule Pack Engine MUST produce deterministic output — identical CFM with identical Rule Pack files MUST produce identical annotated CFM on every execution
- **FR-010**: The Rule Pack Engine MUST operate as a pipeline stage, consuming the CFM via the `CanonicalModelBuilt` event and producing the `RulePackApplied` event
- **FR-011**: The Rule Pack Engine MUST support Value Adjustment Factor (VAF) configuration via Rule Packs, including General System Characteristics (GSC) ratings and their influence on the final function point count
- **FR-012**: The Rule Pack Engine MUST support glossary/terminology overrides that customize how function types and complexity levels are named in measurement reports
- **FR-013**: Added rules that reference function types or attributes not present in the current CFM MUST be logged as informational (unused rules) without causing errors
- **FR-014**: Invalid Rule Pack files MUST NOT cause the pipeline to crash — the engine MUST report errors and continue with all valid rules loaded from other Rule Pack files

### Key Entities

- **Rule Pack**: A file containing one or more measurement policies — exclusions, complexity thresholds, VAF configuration, and glossary overrides. Each Rule Pack is self-contained and independently loadable.
- **Applied Rule Record**: An annotation on a CFM element indicating which rule from which Rule Pack was applied, including the rule type (exclusion, threshold override, VAF) and the before/after values.
- **Rule Validation Report**: The output of Rule Pack validation — lists each loaded file, the rules found, any validation errors (skipped rules), and any conflicts detected.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A Rule Pack with 10 exclusion rules and 5 complexity threshold overrides loads and validates within 2 seconds on standard hardware
- **SC-002**: Every function modified by a Rule Pack in the output CFM includes at least one applied rule reference — 100% of modifications must be traceable to a specific rule
- **SC-003**: Running the same pipeline twice with identical CFM and Rule Pack files produces byte-identical annotated CFM output
- **SC-004**: A Rule Pack that excludes 3 specific function types from counting reduces the eligible function count in the output CFM by exactly the number of functions of those types in the input, without modifying the input CFM
- **SC-005**: Invalid Rule Pack files produce descriptive error messages identifying the specific file, line number, and issue — no silent partial application of invalid rules
- **SC-006**: Applying a Rule Pack with custom complexity thresholds to a CFM with 100+ functions completes within 3 seconds
- **SC-007**: Users can inspect the list of active rules and their sources (file path, line range) through the engine's status output

## Assumptions

- Rule Packs use YAML format, consistent with the project's existing configuration approach (ruamel.yaml)
- Rule Pack files are stored in `.specify/rules/` directory, one or more `.yml` files per project
- The Canonical Functional Model (007) provides a stable, well-defined API for reading function types, DET/RET/FTR counts, and complexity ratings
- The Plugin Discovery Registry (003) and Kernel Pipeline Engine (002) provide the stage registration and event dispatch infrastructure that the Rule Pack Engine consumes
- The Measurement Engine (008) consumes the annotated CFM produced by the Rule Pack Engine and respects exclusion markers and custom complexity ratings
- Value Adjustment Factor configuration is an optional capability — the engine applies VAF only when the Rule Pack provides GSC ratings
- Rule Packs are declarative only — no scripting, conditional logic, or function composition is supported in v1
- The engine runs as a single synchronous pipeline stage; real-time Rule Pack updates during pipeline execution are out of scope
