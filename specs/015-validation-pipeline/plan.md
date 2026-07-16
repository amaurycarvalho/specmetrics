# Implementation Plan: Validation Pipeline

**Branch**: `015-validation-pipeline` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/015-validation-pipeline/spec.md`

## Summary

The Validation Pipeline is a pre-measurement quality gate that validates specification documents for structural correctness, mandatory section completeness, and constitutional compliance before they enter the Semantic Measurement Pipeline. It implements the "Fail Fast" invariant (Pipeline Invariant #7 from the constitution) by catching critical errors early.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: markdown-it-py (spec parsing), Pydantic v2 (validation rule models), structlog (structured validation output)

**Storage**: N/A — file-based, no persistent storage required

**Testing**: pytest

**Target Platform**: Linux, macOS, Windows (CLI tool)

**Project Type**: CLI tool — subcommand within existing Typer CLI, operates as an independent pipeline stage

**Performance Goals**: Single spec validation <5s (1000 lines), batch of 50 specs <30s

**Constraints**: Runs before measurement pipeline; must not depend on measurement engine internals; must preserve Layer Independence (XIV)

**Scale/Scope**: Individual spec files up to 1000 lines; batch validation up to 50 files per invocation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: Specification First (I), Evidence First (V), Plugin-Oriented (VIII), Rule Externalization (IX), Layer Independence (XIV), Fail Fast invariant

**Compliance Verifications**:
- [x] Specification First (I): Primary input is a specification document; validation enforces spec quality before measurement
- [x] Evidence First (V): Each validation failure references the specific section/text that caused the failure, preserving traceability
- [x] Canonical Representation (VII): Validation operates on the raw spec document, not the CFM — this is correct since validation is a pre-CFM gate
- [x] Plugin-Oriented (VIII): Validation rules are externalizable as plugins, not hardcoded in the core engine
- [x] Rule Externalization (IX): Validation policies (which sections are mandatory, constitutional rules) are externalized as Rule Packs
- [x] Layer Independence (XIV): The validation pipeline runs independently and communicates only through the validated document output; no dependency on measurement engine internals
- [x] Open by Default (XII): Validation rules and their configuration are documented and standards-based (markdown-it-py spec parsing)

Gate status: **PASS** — No violations detected. All engaged principles are satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/015-validation-pipeline/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   └── validation/
│       ├── __init__.py
│       ├── pipeline.py        # ValidationPipeline orchestrator
│       ├── rules/             # Built-in validation rules
│       │   ├── __init__.py
│       │   ├── structural.py  # Mandatory sections, format checks
│       │   └── constitutional.py # Constitution compliance checks
│       └── models.py          # ValidationRule, ValidationResult, ValidationReport
├── cli/
│   └── commands/
│       └── validate.py        # `specmetrics validate` CLI command
└── tests/
    ├── contract/
    │   └── test_validate_cli.py
    ├── integration/
    │   └── test_validation_pipeline.py
    └── unit/
        └── validation/
            ├── test_structural_rules.py
            └── test_constitutional_rules.py
```

**Structure Decision**: Single project layout. Validation lives in `kernel/validation/` as an independent module, separated from the measurement pipeline per Layer Independence. CLI integration is a thin command wrapper in `cli/commands/`.

## Complexity Tracking

> No complexity violations detected. Gate status: PASS.
