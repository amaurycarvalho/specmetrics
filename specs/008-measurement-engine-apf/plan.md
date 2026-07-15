# Implementation Plan: Measurement Engine Plugin — APF

**Branch**: `008-measurement-engine-apf` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-measurement-engine-apf/spec.md`

## Summary

Implement a deterministic IFPUG/APF function point measurement engine as a discoverable plugin. The engine consumes the Canonical Functional Model (CFM), applies organizational Rule Packs, and produces traceable, explainable function point counts (ILF, EIF, EI, EO, EQ) with complexity ratings based on DET/RET/FTR thresholds. Every measured function preserves evidence references to its originating CFM elements.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**:
- `pydantic` v2 — for CFM model consumption and measurement result models (platform standard)
- `pluggy` or standard Python entry points — for plugin discovery via `specmetrics.plugins.measurement`
- `structlog` — for structured logging (platform standard)

**Storage**: N/A (in-memory measurement; results propagated via pipeline events)

**Testing**: pytest (platform standard)

**Target Platform**: Linux desktop/server (local execution, CLI + MCP)

**Project Type**: Library/Plugin within the SpecMetrics platform (`specmetrics/plugins/measurement/`)

**Performance Goals**: Complete APF count for 10 data groups + 15 functional processes within 5 seconds (SC-001); handle 500+ functions without degradation (SC-007)

**Constraints**:
- Deterministic execution — identical CFM + identical Rule Packs → byte-identical results
- No LLM inference or non-deterministic operations (FR-008)
- Must not modify the input CFM (immutable pipeline invariant)
- Every measured function must preserve evidence trail (FR-007)

**Scale/Scope**: 500+ functions per CFM; single measurement methodology (APF only); SPF/SNAP deferred

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: IV (LLM-Assisted, Deterministic Results), VI (Explainability by Design), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization)

**Compliance Verifications**:
- [x] Specification First: The engine consumes the CFM, which is derived from specifications. It never reads raw spec documents — compliant via Canonical Isolation.
- [x] Evidence First: FR-007 requires every measured function to preserve evidence references to originating CFM elements. Each function point is traceable.
- [x] Canonical Representation: FR-001 restricts the engine to consume only the CFM. No framework-specific artifacts leak into measurement logic.
- [x] Plugin-Oriented: FR-009 requires implementation as a discoverable plugin. The engine registers via Python Entry Points and communicates through Kernel contracts.
- [x] Rule Externalization: FR-004 and FR-005 require Rule Packs as external inputs. Counting policies are never hardcoded; defaults apply only when no Rule Pack is provided.
- [x] Layer Independence: The engine depends only on the CFM model (from F06) and the plugin contract (from F02). It has no knowledge of adapters, extraction, or graph internals.
- [x] Open by Default: Plugin interface and Rule Pack format are documented contracts. Measurement output format is standardized for downstream export/pub plugins.

## Project Structure

### Documentation (this feature)

```text
specs/008-measurement-engine-apf/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # IFPUG standards research and design decisions
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Validation guide
├── contracts/           # Plugin interface contracts
│   └── measurement-plugin-interface.md
└── checklists/
    └── requirements.md  # Quality checklist
```

### Source Code (repository root)

```text
specmetrics/
└── plugins/
    └── measurement/
        └── apf/
            ├── __init__.py
            ├── plugin.py          # Plugin entry point (discovery + registration)
            ├── counter.py         # Function type classification logic
            ├── complexity.py      # IFPUG complexity matrix tables
            ├── models.py          # Pydantic models for measurement results
            ├── rule_applicator.py # Rule Pack processing
            └── explainer.py       # Evidence trail + explanation builder

tests/
├── unit/
│   └── measurement/
│       └── apf/
│           ├── test_counter.py
│           ├── test_complexity.py
│           ├── test_rule_applicator.py
│           └── test_plugin.py
└── integration/
    └── measurement/
        └── apf/
            └── test_full_measurement.py
```

**Structure Decision**: Single plugin under `specmetrics/plugins/measurement/apf/`, following the existing project structure pattern. The APF plugin is one of potentially many measurement plugins under `plugins/measurement/`. Tests mirror the source tree.

## Complexity Tracking

No constitution violations detected. All engaged principles are satisfied by the design decisions documented above.
