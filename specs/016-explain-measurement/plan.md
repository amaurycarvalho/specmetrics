# Implementation Plan: Explain Measurement

**Branch**: `016-explain-measurement` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/016-explain-measurement/spec.md`

## Summary

The Explain Measurement feature provides structured, traceable explanations of measurement results. Users request an explanation for any metric and receive a breakdown showing which specification elements contributed, what evidence supports each count, and which Rule Pack rules were applied — implementing Constitution Principle VI (Explainability by Design).

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Pydantic v2 (data models), NetworkX (evidence graph queries), structlog (structured output)

**Storage**: Evidence Graph (in-memory NetworkX, persisted via graph_persistence.py)

**Testing**: pytest

**Target Platform**: Linux, macOS, Windows (CLI tool + MCP server)

**Project Type**: CLI + library component within existing Typer CLI

**Performance Goals**: Explanation generation <2s for specs with up to 500 identified elements

**Constraints**: Must consume Evidence Graph and CFM without depending on Measurement Engine internals (Layer Independence XIV); explanations must be reproducible from persisted data

**Scale/Scope**: Single measurement explanations for specs up to 500 elements; comparisons between two measurement runs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: Explainability by Design (VI), Evidence First (V), Rule Externalization (IX), Specification First (I), Layer Independence (XIV)

**Compliance Verifications**:
- [x] Specification First (I): Explanations reference specification sections and fragments as the source of truth for all counted elements
- [x] Evidence First (V): Each counted element in an explanation preserves references to its originating evidence (document ID, section, text excerpt) through the Evidence Graph
- [x] Canonical Representation (VII): Explanation logic consumes the Canonical Functional Model and Evidence Graph — not framework-specific artifacts
- [x] Plugin-Oriented (VIII): Explanation formatters and output renderers may be implemented as plugins (exporter pattern)
- [x] Rule Externalization (IX): Applied Rule Pack rules are identified by ID and description in explanations, linking to the external rule definitions
- [x] Layer Independence (XIV): The explanation module reads from the Evidence Graph and CFM via their published interfaces; no dependency on Measurement Engine internals
- [x] Open by Default (XII): Explanation output format is documented and machine-readable (structured JSON)

Gate status: **PASS** — No violations detected. All engaged principles are satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/016-explain-measurement/
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
│   └── explanation/
│       ├── __init__.py
│       ├── service.py            # ExplainService orchestration
│       ├── models.py             # MeasurementExplanation, MetricExplanation, etc.
│       ├── evidence_tracer.py    # Evidence graph traversal for traceability
│       ├── comparison.py         # ExplanationComparison logic
│       └── formatters/           # Output renderers
│           ├── __init__.py
│           ├── text.py           # Human-readable text format
│           └── json.py           # Machine-readable JSON format
├── cli/
│   └── commands/
│       └── explain.py            # `specmetrics explain` CLI command
├── mcp/
│   └── tools/
│       └── explain_tool.py       # MCP tool for explanation requests
└── tests/
    ├── contract/
    │   └── test_explain_cli.py   # CLI contract tests
    ├── integration/
    │   └── test_explain_service.py  # End-to-end explanation flow
    └── unit/
        └── explanation/
            ├── test_service.py
            ├── test_evidence_tracer.py
            └── test_comparison.py
```

**Structure Decision**: Explanation lives in `kernel/explanation/` as an independent module following the same pattern as `kernel/validation/`. It consumes the Evidence Graph and CFM through their public interfaces. CLI and MCP are thin wrappers. Tests mirror the existing per-module structure.

## Complexity Tracking

> No complexity violations detected. Gate status: PASS.
