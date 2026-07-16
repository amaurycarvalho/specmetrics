# Implementation Plan: Measurement Engine Plugin — SFP

**Branch**: `017-measurement-engine-sfp` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/017-measurement-engine-sfp/spec.md`

## Summary

Implement a deterministic Simple Function Points (SFP) measurement engine as a discoverable SpecMetrics plugin. The engine consumes the Canonical Functional Model (CFM), identifies Functional Processes and Logical Functions via node type/attribute matching, applies organizational Rule Packs, and produces traceable, explainable SFP counts with fixed contribution values per component type. Every measured component preserves evidence references to its originating CFM elements.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**:
- `pydantic` v2 — for CFM model consumption and measurement result models (platform standard)
- `pluggy` or standard Python entry points — for plugin discovery via `specmetrics.plugins.measurement`
- `structlog` — for structured logging (platform standard)
- `opentelemetry-api` — for measurement duration histogram and component count gauges (platform standard)

**Storage**: N/A (in-memory measurement; results propagated via pipeline events)

**Testing**: pytest (platform standard)

**Target Platform**: Linux desktop/server (local execution, CLI + MCP)

**Project Type**: Library/Plugin within the SpecMetrics platform (`specmetrics/plugins/measurement/`)

**Performance Goals**: Complete SFP count for medium-sized CFMs (≤500 Functional Processes, ≤300 Logical Functions) within 5 seconds (SC-003); handle 1000+ Functional Processes with ≤15% deviation per doubling (SC-007)

**Constraints**:
- Deterministic execution — identical CFM + identical Rule Packs → byte-identical results
- No LLM inference or non-deterministic operations (FR-002)
- Must not modify the input CFM (immutable pipeline invariant)
- Only two component types: Functional Processes and Logical Functions
- No complexity classification (FR-021 to FR-026)
- Fixed contribution values per component type (FR-019, FR-020) — specific values sourced from licensed IFPUG SFP specification
- Every measured component must preserve evidence trail (FR-033)

**Scale/Scope**: Single measurement methodology (SFP only); FPA/SNAP are separate plugins

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: IV (LLM-Assisted, Deterministic Results), VI (Explainability by Design), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization)

**Compliance Verifications**:
- [x] Specification First: The engine consumes the CFM, which is derived from specifications. It never reads raw spec documents — compliant via Canonical Isolation.
- [x] Evidence First: FR-033 requires every measured component to expose originating CFM node, specification, applied rule, and contribution. Each component is traceable.
- [x] Canonical Representation: FR-001 restricts the engine to consume only the CFM. No framework-specific artifacts leak into measurement logic.
- [x] Plugin-Oriented: FR-007 requires implementation as a discoverable plugin. The engine registers via Python Entry Points and communicates through Kernel contracts.
- [x] Rule Externalization: FR-005 and FR-028–FR-032 require Rule Packs as external inputs. Counting policies are never hardcoded; defaults apply only when no Rule Pack is provided.
- [x] Layer Independence: The engine depends only on the CFM model (from F06) and the plugin contract (from F02). It has no knowledge of adapters, extraction, or graph internals.
- [x] Open by Default: Plugin interface and Rule Pack format are documented contracts. Measurement output format is standardized for downstream export/pub plugins.

## Project Structure

### Documentation (this feature)

```text
specs/017-measurement-engine-sfp/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # SFP methodology research and design decisions
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Validation guide
├── contracts/
│   └── measurement-plugin-interface.md
└── checklists/
    └── requirements.md  # Quality checklist
```

### Source Code (repository root)

```text
specmetrics/
└── plugins/
    └── measurement/
        └── sfp/
            ├── __init__.py
            ├── plugin.py          # Plugin entry point (discovery + registration)
            ├── counter.py         # Component identification and counting logic
            ├── models.py          # Pydantic models for measurement results
            ├── rule_applicator.py # Rule Pack processing
            └── explainer.py       # Evidence trail + explanation builder

tests/
├── unit/
│   └── measurement/
│       └── sfp/
│           ├── test_counter.py
│           ├── test_rule_applicator.py
│           └── test_plugin.py
└── integration/
    └── measurement/
        └── sfp/
            └── test_full_measurement.py
```

**Structure Decision**: Single plugin under `specmetrics/plugins/measurement/sfp/`, following the existing FPA plugin pattern. SFP shares the same project infrastructure as FPA but uses simplified identification rules and a two-component measurement model.

## Complexity Tracking

No constitution violations detected. All engaged principles are satisfied by the design decisions documented above.
