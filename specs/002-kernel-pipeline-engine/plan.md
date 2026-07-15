# Implementation Plan: Kernel & Pipeline Engine

**Branch**: `002-kernel-pipeline-engine` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-kernel-pipeline-engine/spec.md`

## Summary

Implement the Pipeline Engine and Event Bus that orchestrate the SpecMetrics
Semantic Measurement Pipeline. The engine manages execution lifecycle, publishes
immutable domain events, enforces canonical stage order, collects pipeline
context, and ensures fail-fast deterministic execution. It communicates
exclusively through an in-process synchronous Event Bus with no external
dependencies.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: structlog (logging), pytest (testing)

**Storage**: N/A — pipeline context is in-memory; no persistence required

**Testing**: pytest (unit + integration for pipeline sequences)

**Target Platform**: Linux (local CLI execution)

**Project Type**: library (kernel module within a CLI application)

**Performance Goals**: Stage failure reported within 1 second (SC-002); pipeline
completion or failure notification within 5 seconds (SC-005)

**Constraints**: In-process only, no external messaging, synchronous event
delivery, single-threaded per execution, immutable Pipeline Context between
stages

**Scale/Scope**: Single pipeline execution at a time per invocation; concurrent
executions produce isolated contexts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: III (Semantic Before Structural), IV (LLM-Assisted,
Deterministic Results), V (Evidence First), VII (Canonical Representation),
VIII (Plugin-Oriented), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First: Not directly — this feature orchestrates pipeline
  stages that consume specifications; compliance verified via consuming stages
- [x] Evidence First: Pipeline Context preserves evidence references throughout
  the execution
- [x] Canonical Representation: Pipeline enforces that downstream components
  receive only the CFM, never raw framework documents
- [x] Plugin-Oriented: All pipeline stages are pluggable; the engine is
  stage-agnostic
- [x] Rule Externalization: Not directly — delegated to Rule Pack Engine stage
- [x] Layer Independence: Pipeline Engine depends only on stable event
  contracts, never on stage implementation details
- [x] Open by Default: Event schemas and handler registration interfaces are
  documented public contracts

**Gate result**: PASS — all principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/002-kernel-pipeline-engine/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── __init__.py
│   ├── pipeline_engine.py    # Pipeline Engine orchestrator
│   ├── event_bus.py          # Synchronous in-process Event Bus
│   ├── pipeline_context.py   # Pipeline Context data structure
│   ├── events.py             # Event type definitions and schemas
│   └── handler_registry.py   # Event handler registration & resolution
├── application/
│   └── __init__.py
└── tests/
    ├── unit/
    │   ├── test_pipeline_engine.py
    │   ├── test_event_bus.py
    │   └── test_pipeline_context.py
    └── integration/
        └── test_pipeline_execution.py
```

**Structure Decision**: Files live under `specmetrics/kernel/` per the
constitution's project structure. Tests mirror the source layout under
`tests/unit/` and `tests/integration/`.

## Complexity Tracking

No constitution violations to justify.
