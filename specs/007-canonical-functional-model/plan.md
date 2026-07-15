# Implementation Plan: Canonical Functional Model Builder

**Branch**: `main` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-canonical-functional-model/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Build the Canonical Functional Model (CFM) pipeline stage — the fifth stage in the SpecMetrics measurement pipeline. It receives `EvidenceGraph` from the Evidence Graph stage (F05), transforms extracted semantic elements into a framework-independent Canonical Functional Model containing Actors, Functional Processes, Business Rules, Data Groups, Relationships, and Operations, and emits a `CanonicalModelBuilt` event. The CFM is the boundary between framework-specific extraction and deterministic measurement — no downstream component ever sees framework-specific concepts.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Pydantic v2 (data models), NetworkX (graph input consumed, not used internally — CFM is a domain model, not a graph)

**Storage**: In-memory data structure with optional serialization for debugging/inspection. No persistent database — the CFM is rebuilt each pipeline run.

**Testing**: pytest (project standard) — contract tests for CFM interface, integration tests for pipeline stage wiring, unit tests for classification logic

**Target Platform**: Linux — local execution (CLI + MCP Server, per Release 0.1 deployment model)

**Project Type**: Library — core pipeline stage within the `specmetrics` package, not a standalone service

**Performance Goals**: Transform 500 evidence graph elements into CFM in under 3 seconds on a standard development machine (SC-001)

**Constraints**: Must be deterministic (same input → identical CFM), immutable output, no framework-specific labels in model (per FR-003, FR-007)

**Scale/Scope**: Pipeline stage processing the output of the Evidence Graph stage (F05) — element count bounded by specification document size (typically hundreds to low thousands of semantic elements per repository)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: VII (Canonical Representation), XIV (Layer Independence), V (Evidence First), I (Specification First), II (Specification as a Measurable Asset)

**Compliance Verifications**:
- [x] **Specification First (I)**: The CFM Builder consumes the EvidenceGraph, which is built exclusively from software specifications. It never reads source code or implementation artifacts.
- [x] **Evidence First (V)**: Every CFM element preserves its evidence reference chain (document ID, section ID, text fragment). No element exists in the CFM without traceable provenance.
- [x] **Canonical Representation (VII)**: The CFM is the canonical boundary — no framework-specific concept survives beyond this stage. Downstream consumers interact only with framework-independent Actors, Functional Processes, Business Rules, Data Groups, Relationships, and Operations.
- [x] **Layer Independence (XIV)**: The CFM Builder depends only on the `EvidenceGraph` contract (produced by F05) and exposes the `CanonicalFunctionalModel` contract (consumed by F07 and F09). No direct coupling between adjacent layers.
- [x] **Specification as a Measurable Asset (II)**: The CFM transforms extracted semantic knowledge into a structured, reusable model that feeds deterministic measurement — reifying the spec-as-asset principle.
- [x] **Plugin-Oriented (VIII)**: The CFM Builder is a core pipeline stage, not a plugin extension point. However, its output contract (CFM) is the interface that measurement engine plugins consume — enabling plugin independence from framework specifics.
- [x] **Open by Default (XII)**: The CFM interface is a documented, framework-agnostic contract. Any measurement methodology plugin can consume it without proprietary knowledge.
- [x] **Explainability by Design (VI)**: CFM elements preserve full evidence traceability, enabling downstream explainability of measurements through the evidence chain.

**Gate Decision**: All compliance checks pass. No violations or unjustified complexity.

*Post-design re-check (Phase 1 completed): All checks still pass. The design introduces no new coupling, no framework-specific dependencies, and preserves full evidence traceability.*

## Project Structure

### Documentation (this feature)

```text
specs/007-canonical-functional-model/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── __init__.py
│   ├── pipeline.py          # Pipeline orchestration (existing, extended)
│   ├── events.py            # Domain events (existing, extended with CanonicalModelBuilt)
│   └── cfm/
│       ├── __init__.py
│       ├── model.py          # CanonicalFunctionalModel and entity definitions
│       ├── builder.py        # CFM Builder stage — transforms EvidenceGraph → CFM
│       ├── classifier.py     # Evidence graph node → CFM category classification logic
│       └── metadata.py       # BuildMetadata and diagnostic types
├── infrastructure/
│   └── serialization/
│       └── cfm_serializer.py # CFM serialization/deserialization (debug/inspection)
└── tests/
    ├── contract/
    │   └── test_cfm_interface.py    # Contract tests for CFM public interface
    ├── integration/
    │   └── test_cfm_pipeline_stage.py # Pipeline stage wiring tests
    └── unit/
        ├── test_cfm_builder.py      # Builder unit tests
        ├── test_cfm_classifier.py   # Classification logic unit tests
        └── test_cfm_model.py        # Model validation unit tests
```

**Structure Decision**: Core pipeline stage under `kernel/cfm/` following the layered architecture defined in the constitution. The CFM is a kernel-level component — not a plugin — because it enforces the canonical boundary that all measurement plugins depend on. Tests follow the project's `contract/integration/unit` convention.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations to justify.

## Phase 0: Research & Outline

No NEEDS CLARIFICATION markers exist in the spec — all design decisions were resolved using project context and constitution principles. Research is limited to confirming established technology choices from the project's documented stack.

### Research Tasks

| Task | Scope | Source |
|------|-------|--------|
| Pydantic v2 patterns for immutable domain models | Confirm patterns matching existing `kernel/` codebase | Constitution: Pydantic v2 |
| Pipeline stage integration pattern | Review existing pipeline stage (Evidence Graph F05) for event emission and stage contract conventions | Existing codebase |

**Output**: [research.md](research.md)

## Phase 1: Design & Contracts

**Prerequisites**: research.md complete

### Artifacts

| Artifact | Description |
|----------|-------------|
| [data-model.md](data-model.md) | CanonicalFunctionalModel entity definitions, fields, relationships, validation rules, state transitions |
| [contracts/](contracts/) | CFM public interface contracts — the contract that downstream measurement engine plugins depend on |
| [quickstart.md](quickstart.md) | Runnable validation scenarios proving the CFM Builder works end-to-end |
